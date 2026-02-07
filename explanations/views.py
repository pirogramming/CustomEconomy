# explanations/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from articles.models import Article
from .models import ArticleExplanation
from .utils import GeminiFinancialTutor
from accounts.models import UserInterest, Interest
from django.utils import timezone
import os
import json
import re
from django.conf import settings
from quizzes.services import create_ai_quiz_from_article
import threading
from django.db.models import Q, F, Case, When, Value, FloatField

def explanation_detail(request, article_id):
    """기사 상세 페이지 (원문만 표시, AI는 나중에 AJAX로 로드)"""
    
    # 1. 기사 가져오기
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. URL 파라미터에서 레벨 가져오기
    selected_level = int(request.GET.get('level', 0))
    
    # 3. 추천 점수 로직
    user = request.user
    if user.is_authenticated and selected_level == 0:
        target_interests = article.sub_interests.all()
        
        if target_interests.exists():
            # (1) 관심 분야 점수 +2 (30점 상한은 모델 save에서 처리)
            for interest_obj in target_interests:
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                ui.interest_score += 2
                ui.save() 
                
            # (2) 나머지 분야 점수 -0.5 (관심사 순위 교체)
            UserInterest.objects.filter(user=user).exclude(
                interest__in=target_interests
            ).update(
                interest_score=Case(
                    When(interest_score__lte=0.5, then=Value(0)),
                    default=F('interest_score') - Value(0.5),
                    output_field=FloatField() # 또는 IntegerField
                )
            )
    
    # 4. 사용자 정보
    if request.user.is_authenticated:
        user_interests = list(UserInterest.objects.filter(
            user=user, 
            is_selected=True
        ).values_list('interest__name', flat=True))
        if not user_interests:
            user_interests = ["소비"]
        user_level = 5 if request.user.is_superuser else getattr(request.user, 'level', 1)
    else:
        user_interests = ["소비"]
        user_level = 4
    
    # 5. 이미 생성된 해설만 조회 (생성하지 않음!)
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
    
    # 6. 단어 추출 로직
    related_words = []
    try:
        json_path = os.path.join(settings.BASE_DIR, 'scripts', 'data', 'master_dictionary.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                master_dict = json.load(f)
            
            full_text = f"{article.title} {article.content}"
            
            for word, definition in master_dict.items():
                safe_word = re.escape(word)
                if re.search(safe_word, full_text, re.IGNORECASE):
                    related_words.append({
                        'word': word,
                        'definition': definition
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
    }
    
    return render(request, 'ai_explain.html', context)


def generate_level_explanation(request, article_id, level):
    """
    AJAX 요청으로 특정 레벨의 AI 해석만 생성
    GET /explanations/<article_id>/generate/<level>/
    """
    
    if request.method != 'GET':
        return JsonResponse({'error': 'GET 요청만 허용됩니다.'}, status=405)
    
    # 1. 기사 가져오기
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. 레벨 검증
    try:
        level = int(level)
        if level < 1 or level > 5:
            return JsonResponse({'error': '레벨은 1~5 사이여야 합니다.'}, status=400)
    except ValueError:
        return JsonResponse({'error': '잘못된 레벨 값입니다.'}, status=400)
    
    # 3. 사용자 권한 확인
    user = request.user
    if user.is_authenticated:
        user_interests = list(UserInterest.objects.filter(
            user=user, 
            is_selected=True
        ).values_list('interest__name', flat=True))
        if not user_interests:
            user_interests = ["소비"]
        user_level = 5 if user.is_superuser else getattr(user, 'level', 1)
    else:
        user_interests = ["소비"]
        user_level = 4
    
    # 권한 체크
    if level > user_level:
        return JsonResponse({
            'error': f'레벨 {level}은 잠겨있습니다. 현재 레벨: {user_level}'
        }, status=403)
    
    # 4. 이미 생성되었는지 확인
    existing = ArticleExplanation.objects.filter(
        article=article,
        level=level
    ).first()
    
    if existing:
        # 이미 있으면 바로 반환
        return JsonResponse({
            'success': True,
            'cached': True,
            'level': level,
            'data': {
                'article_explanation': existing.article_explanation,
                'term_explanation': existing.term_explanation,
                'prediction': existing.prediction,
            }
        })
    
    # 5. AI 생성 (해당 레벨만!)
    print(f"🚀 레벨 {level} AI 생성 시작...")
    
    category_name = article.category.name if article.category else "경제"
    
    tutor = GeminiFinancialTutor()
    analysis_data = tutor.generate_single_level_analysis(
        text=article.content,
        category=category_name,
        interests=user_interests,
        target_level=level  # 👈 특정 레벨만 생성!
    )
    
    if not analysis_data:
        return JsonResponse({'error': 'AI 생성 실패'}, status=500)
    
    # 6. DB 저장
    try:
        with transaction.atomic():
            content_text = analysis_data.get('storytelling', '내용 없음')
            
            terms_list = analysis_data.get('terms', [])
            if isinstance(terms_list, list) and terms_list:
                term_text = "\n\n".join([
                    f"📌 {item.get('term', '용어')}\n{item.get('explanation', '설명 없음')}"
                    for item in terms_list
                ])
            else:
                term_text = "용어 설명 없음"
            
            pred_text = analysis_data.get('advice', '전망 없음')
            
            explanation = ArticleExplanation.objects.create(
                article=article,
                level=level,
                article_explanation=content_text,
                term_explanation=term_text,
                prediction=pred_text
            )
            
            print(f"✅ 레벨 {level} 저장 완료")

            #------------------------------------
            # 퀴즈 생성 추가 (백그라운드에서 생성중)
            thread = threading.Thread(target=create_ai_quiz_from_article, args=(article,))
            thread.start()
            #------------------------------------
            
            return JsonResponse({
                'success': True,
                'cached': False,
                'level': level,
                'data': {
                    'article_explanation': explanation.article_explanation,
                    'term_explanation': explanation.term_explanation,
                    'prediction': explanation.prediction,
                }
            })
            
    except Exception as e:
        print(f"❌ DB 저장 실패: {e}")
        return JsonResponse({'error': f'DB 저장 실패: {str(e)}'}, status=500)
    # -----------------------------------------------------------
    # [시현 영역] 단어 추출 로직 (정규표현식 기반 매칭 강화 버전)
    # -----------------------------------------------------------
    related_words = []
    import os, json, re
    from django.conf import settings

    try:
        json_path = os.path.join(settings.BASE_DIR, 'scripts', 'data', 'master_dictionary.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                master_dict = json.load(f)
            
            # 1. 분석 대상 텍스트 통합 (제목 + 본문)
            # 본문뿐만 아니라 제목에 있는 핵심 단어도 놓치지 않도록 합칩니다.
            full_text = f"{article.title} {article.content}"
            
            # 2. 매칭 루프
            for word, definition in master_dict.items():
                # 특수문자가 포함된 단어(예: LTV/DTI)를 안전하게 찾기 위해 escape 처리
                safe_word = re.escape(word)
                
                # 정규표현식 설명: 
                # 본문에 단어가 포함되어 있는지 확인 (앞뒤에 조사가 붙어도 찾을 수 있게 함)
                # re.IGNORECASE: 대소문자 무시
                if re.search(safe_word, full_text, re.IGNORECASE):
                    related_words.append({
                        'word': word,
                        'definition': definition
                    })
            
            # 3. 가나다순 정렬
            related_words.sort(key=lambda x: x['word'])

            # --- [최종 확인용 디버깅 로그] ---
            print(f"✅ [디버깅] 분석한 기사: {article.title[:20]}...")
            print(f"✅ [디버깅] 찾아낸 단어 개수: {len(related_words)}개")
            if related_words:
                print(f"✅ [디버깅] 매칭된 단어 샘플: {[w['word'] for w in related_words[:5]]}")
            else:
                print("⚠️ [디버깅] 매칭된 단어가 하나도 없습니다. 본문 내용을 확인해보세요.")
                # 본문이 비어있지는 않은지 마지막 확인
                print(f"⚠️ [디버깅] 본문 데이터 존재 여부: {bool(article.content)}")
            # -------------------------------

    except Exception as e:
        print(f"❌ 단어 추출 중 에러 발생: {e}")
    # -----------------------------------------------------------
    context = {
        'article': article,
        'explanations': explanations,
        'selected_level': selected_level,  # 이게 중요! JavaScript에서 사용
        'user_level': user_level,
        'related_words': related_words,
    }
    
    return render(request, 'ai_explain.html', context)