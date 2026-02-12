# explanations/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from articles.models import Article
from .models import ArticleExplanation, InterestBasedPrediction
from .utils import GeminiFinancialTutor
from accounts.models import UserInterest, Interest
from django.utils import timezone
import os
import json
import re
from django.conf import settings
from quizzes.services import create_ai_quiz_from_article
import threading
from django.db.models import Q, F, Case, When, Value, IntegerField
from quizzes.models import Quiz

# ⭐ 전체 관심사 목록 (수정됨)
ALL_INTERESTS = ['투자', '부동산', '대출/금융', '소비', '환율/해외', '세금/정책', '자영업/사업자', '취업/고용']

def explanation_detail(request, article_id):
    """기사 상세 페이지"""
    
    article = get_object_or_404(Article, pk=article_id)
    selected_level = int(request.GET.get('level', 0))
    
    user = request.user
    if user.is_authenticated and selected_level == 0:
        target_interests = article.sub_interests.all()
        
        if target_interests.exists():
            for interest_obj in target_interests:
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                ui.interest_score += 2
                ui.last_viewed_at = timezone.now()
                ui.save() 
                
            UserInterest.objects.filter(user=user).exclude(
                interest__in=target_interests
            ).update(
                interest_score=Case(
                    When(interest_score__lte=0.5, then=Value(0)),
                    default=F('interest_score') - Value(1),
                    output_field=IntegerField()
                )
            )
    
    # 사용자 관심사 추출
    if request.user.is_authenticated:
        user_interest_names = list(UserInterest.objects.filter(
            user=user, 
            is_selected=True
        ).values_list('interest__name', flat=True))
        
        if not user_interest_names:
            user_interest_names = ["투자"]  # 기본값
        
        user_level = 5 if request.user.is_superuser else getattr(request.user, 'level', 1)
    else:
        # 비로그인 기본값
        user_interest_names = ["투자"]
        user_level = 4
    
    if not request.user.is_authenticated:
        explanations = ArticleExplanation.objects.filter(
            article=article, 
            level=4
        ).order_by('level')
    else:
        explanations = ArticleExplanation.objects.filter(
            article=article, 
            level__lte=user_level
        ).order_by('level')
    
    # 단어 추출 로직
    related_words = []
    try:
        json_path = os.path.join(settings.BASE_DIR, 'scripts', 'data', 'master_dictionary.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                master_dict = json.load(f)
            
            full_text = f"{article.title} {article.content}"
            
            from terms.models import Term, TermBookmark

            for word, definition in master_dict.items():
                safe_word = re.escape(word)
                if re.search(safe_word, full_text, re.IGNORECASE):
                    # Check if a Term exists and whether current user bookmarked it
                    term_obj = Term.objects.filter(name=word).first()
                    bookmarked = False
                    term_id = None
                    if term_obj:
                        term_id = term_obj.id
                        if request.user.is_authenticated:
                            bookmarked = TermBookmark.objects.filter(user=request.user, term=term_obj).exists()

                    related_words.append({
                        'word': word,
                        'definition': definition,
                        'bookmarked': bookmarked,
                        'term_id': term_id,
                    })
            
            related_words.sort(key=lambda x: x['word'])
            print(f"✅ 찾아낸 단어 개수: {len(related_words)}개")
    except Exception as e:
        print(f"❌ 단어 추출 중 에러: {e}")
    
    context = {
        'article': article,
        'explanations': explanations,
        'selected_level': selected_level,
        'user_level': user_level,
        'related_words': related_words,
        'user_interests': user_interest_names,
    }
    
    return render(request, 'ai_explain.html', context)


def generate_level_explanation(request, article_id, level):
    """
    ⭐⭐⭐ AJAX 요청으로 특정 레벨의 AI 해석 생성 ⭐⭐⭐
    
    첫 사용자: AI 1회 호출로 해설 + 8개 관심사 전망 전부 생성 (10초)
    이후 사용자: DB 조회만 (2초)
    """
    
    if request.method != 'GET':
        return JsonResponse({'error': 'GET 요청만 허용됩니다.'}, status=405)
    
    article = get_object_or_404(Article, pk=article_id)
    
    try:
        level = int(level)
        if level < 1 or level > 5:
            return JsonResponse({'error': '레벨은 1~5 사이여야 합니다.'}, status=400)
    except ValueError:
        return JsonResponse({'error': '잘못된 레벨 값입니다.'}, status=400)
    
    # 사용자 정보
    user = request.user
    if user.is_authenticated:
        user_interest_names = list(UserInterest.objects.filter(
            user=user, 
            is_selected=True
        ).values_list('interest__name', flat=True))
        
        if not user_interest_names:
            user_interest_names = ["투자"]
        
        user_level = 5 if user.is_superuser else getattr(user, 'level', 1)
    else:
        user_interest_names = ["투자"]
        user_level = 4
    
    if level > user_level:
        return JsonResponse({
            'error': f'레벨 {level}은 잠겨있습니다. 현재 레벨: {user_level}'
        }, status=403)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔥 1단계: 공통 해설 + 8개 전망 생성 (첫 사용자만)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    explanation, explanation_created = ArticleExplanation.objects.get_or_create(
        article=article,
        level=level,
        defaults={
            'article_explanation': '',
            'term_explanation': '',
            'prediction': ''
        }
    )
    
    # 첫 생성이거나 해설이 비어있으면 AI 생성
    if explanation_created or not explanation.article_explanation:
        print(f"🚀 레벨 {level} 전체 AI 생성 시작...")
        
        category_name = article.category.name if article.category else "경제"
        tutor = GeminiFinancialTutor()
        
        # ⭐ AI 1회 호출로 해설 + 8개 전망 전부 생성
        analysis_data = tutor.generate_full_analysis_with_all_interests(
            text=article.content,
            category=category_name,
            target_level=level,
            all_interests=ALL_INTERESTS  # 8개 전부
        )
        
        if not analysis_data:
            return JsonResponse({'error': 'AI 생성 실패'}, status=500)
        
        with transaction.atomic():
            # 해설 저장
            explanation.article_explanation = analysis_data.get('storytelling', '내용 없음')
            
            terms_list = analysis_data.get('terms', [])
            if isinstance(terms_list, list) and terms_list:
                explanation.term_explanation = "\n\n".join([
                    f"📌 {item.get('term', '용어')}\n{item.get('explanation', '설명 없음')}"
                    for item in terms_list
                ])
            else:
                explanation.term_explanation = "용어 설명 없음"
            
            explanation.save()
            print(f"✅ 레벨 {level} 공통 해설 저장 완료")
            
            # ⭐ 8개 관심사 전망 전부 저장
            predictions_dict = analysis_data.get('predictions', {})
            
            for interest_name in ALL_INTERESTS:
                prediction_text = predictions_dict.get(interest_name, '전망 없음')
                
                InterestBasedPrediction.objects.update_or_create(
                    explanation=explanation,
                    interest=interest_name,
                    defaults={'prediction_text': prediction_text}
                )
            
            print(f"✅ 레벨 {level} 8개 관심사 전망 전부 저장 완료")
    else:
        print(f"✅ 레벨 {level} 이미 생성됨 (캐시 사용)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔥 2단계: 사용자 관심사에 맞는 전망만 선택
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # AI가 기사와 가장 관련 깊은 관심사 선택
    tutor = GeminiFinancialTutor()
    best_interest_data = tutor.select_best_interest_from_user_list(
        text=article.content,
        user_interests=user_interest_names
    )
    
    selected_interest = best_interest_data.get('selected_interest', user_interest_names[0])
    
    # DB에서 해당 관심사 전망 조회
    prediction = InterestBasedPrediction.objects.filter(
        explanation=explanation,
        interest=selected_interest
    ).first()
    
    if not prediction:
        # 혹시 없으면 첫 번째 관심사로 대체
        prediction = InterestBasedPrediction.objects.filter(
            explanation=explanation,
            interest=user_interest_names[0]
        ).first()
        selected_interest = user_interest_names[0]

    # 퀴즈 생성 (백그라운드에서)
    if not Quiz.objects.filter(article=article, type='A').exists():
        thread = threading.Thread(target=create_ai_quiz_from_article, args=(article,))
        thread.daemon = True  # 서버 종료 시 함께 종료되도록 설정
        thread.start()
    
    # 응답 반환
    return JsonResponse({
        'success': True,
        'cached': not explanation_created,
        'level': level,
        'interest': selected_interest,  # AI가 선택한 관심사
        'data': {
            'article_explanation': explanation.article_explanation,
            'term_explanation': explanation.term_explanation,
            'prediction': prediction.prediction_text if prediction else '전망 없음',
        }
    })