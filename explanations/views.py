# explanations/views.py
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from articles.models import Article
from .models import ArticleExplanation
from .utils import GeminiFinancialTutor
from accounts.models import UserInterest, Interest
from django.utils import timezone

def explanation_detail(request, article_id):
    # 1. 기사 가져오기
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. URL 파라미터에서 레벨 가져오기 (?level=1)
    selected_level = int(request.GET.get('level', 0))  # 0이면 원문

    # 추천을 위한 점수 로직 추가
    user = request.user
    if user.is_authenticated and selected_level == 0:
        for interest_obj in article.sub_interests.all():
            ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
            ui.interest_score += 2
            ui.save()
    
    # 3. 사용자 정보
    if request.user.is_authenticated:
        user_interests = list(UserInterest.objects.filter(user=user, is_selected=True).values_list('interest__name', flat=True))
        if not user_interests:
            user_interests = ["소비"]
        user_level = 5 if request.user.is_superuser else getattr(request.user, 'level', 1)
    else:
        user_interests = ["소비"]
        user_level = 4
    
    # 4. DB에서 해설 조회
    # 모든 데이터를 다 가져오는 것이 아니라, 사용자의 레벨 이하만 조회합니다.
    if not request.user.is_authenticated:
        # 비로그인: 정확히 레벨 4인 해설만 가져옴
        explanations = ArticleExplanation.objects.filter(
            article=article, 
            level=4
        ).order_by('level')
    else:
        # 로그인 유저: 내 레벨 이하(__lte) 전부 가져옴
        explanations = ArticleExplanation.objects.filter(
            article=article, 
            level__lte=user_level
        ).order_by('level')
        
    # 5. 해설이 없으면 AI 생성
    if not explanations.exists():
        print(f"🤖 '{article.title}' AI 분석 시작...")
        
        category_name = article.category.name if article.category else "경제"
        
        tutor = GeminiFinancialTutor()
        analysis_data = tutor.generate_analysis(
            text=article.content,
            category=category_name,
            interests=user_interests
        )
        
        if analysis_data:
            with transaction.atomic():
                for data in analysis_data:
                    level = data.get('level', 1)
                    
                    content_text = data.get('storytelling', '내용 없음')
                    
                    terms_list = data.get('terms', [])
                    if isinstance(terms_list, list) and terms_list:
                        term_text = "\n\n".join([
                            f"📌 {item.get('term', '용어')}\n{item.get('explanation', '설명 없음')}"
                            for item in terms_list
                        ])
                    else:
                        term_text = "용어 설명 없음"
                    
                    pred_text = data.get('advice', '전망 없음')

                    ArticleExplanation.objects.create(
                        article=article,
                        level=level,
                        article_explanation=content_text,
                        term_explanation=term_text,
                        prediction=pred_text
                    )
                
                print("✅ AI 분석 완료")
                explanations = ArticleExplanation.objects.filter(
                    article=article, 
                    level__lte=user_level
                ).order_by('level')

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