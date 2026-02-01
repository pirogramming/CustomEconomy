# explanations/views.py
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from articles.models import Article  # 팀원 앱의 모델 import
from .models import ArticleExplanation
from .utils import GeminiFinancialTutor

def explanation_detail(request, article_id):
    # 1. 기사 가져오기 (팀원 앱의 Article 모델 사용)
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. URL 파라미터에서 레벨 가져오기 (?level=1)
    selected_level = int(request.GET.get('level', 1))
    
    # 3. 사용자 정보
    if request.user.is_authenticated:
        user_interests = ["부동산", "주식"]
        user_level = 5 if request.user.is_superuser else getattr(request.user, 'level', 1)
    else:
        user_interests = ["부동산", "주식"]
        user_level = 5
    
    # 4. DB에서 해설 조회
    explanations = ArticleExplanation.objects.filter(article=article).order_by('level')
    
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
                # 다시 조회
                explanations = ArticleExplanation.objects.filter(article=article).order_by('level')
    
    # 6. 선택된 레벨의 해설 가져오기
    current_explanation = explanations.filter(level=selected_level).first()
    
    context = {
        'article': article,
        'explanations': explanations,
        'current_explanation': current_explanation,
        'selected_level': selected_level,
        'user_level': user_level,
    }
    
    return render(request, 'ai_explain.html', context)