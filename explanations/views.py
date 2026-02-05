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
    
    context = {
        'article': article,
        'explanations': explanations,
        'selected_level': selected_level,  # 이게 중요! JavaScript에서 사용
        'user_level': user_level,
    }
    
    return render(request, 'ai_explain.html', context)