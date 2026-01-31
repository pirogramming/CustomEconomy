from django.shortcuts import render, get_object_or_404
from django.db import transaction
from articles.models import Article
from explanations.models import ArticleExplanation
from .utils import GeminiFinancialTutor

def explanation_detail(request, article_id):
    # 1. 기사 객체 가져오기
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. 사용자 정보 설정 (로그인 여부 체크)
    if request.user.is_authenticated:
        # UserInterest 모델을 통해 관심사 이름 리스트 추출
        user_interests = list(request.user.interests.values_list('name', flat=True))
        if not user_interests:
            user_interests = ["경제 일반"]
        user_level = request.user.level
    else:
        # [TEST MODE] 비로그인 유저를 위한 더미 데이터
        print("📢 [Test] 비로그인 유저: 관심사(부동산, 주식), 레벨(5)로 설정됨")
        user_interests = ["부동산", "주식"]
        user_level = 5

    # 3. DB에 이미 생성된 해설이 있는지 확인
    explanations = ArticleExplanation.objects.filter(article=article).order_by('level')
    
    # 4. 해설이 없다면? -> AI 분석 시작 (최초 1회)
    if not explanations.exists():
        # [수정 완료] 예외 처리 구문 띄어쓰기 수정
        try:
            # Article 모델의 category가 ForeignKey라면 .name으로 접근
            category_name = article.category.name if article.category else "경제"
        except AttributeError:
            category_name = "경제" # 예외 처리 (category 필드가 없거나 모델 구조가 다를 때)

        print(f"🤖 '{article.title}' AI 분석 시작 (카테고리: {category_name})...")
        tutor = GeminiFinancialTutor()
        
        # AI 호출
        analysis_data = tutor.generate_analysis(
            text=article.content,
            category=category_name,
            interests=user_interests
        )

        # DB 저장 (트랜잭션으로 안전하게)
        if analysis_data:
            with transaction.atomic():
                new_explanations = []
                for data in analysis_data:
                    expl = ArticleExplanation.objects.create(
                        article=article,
                        level=data['level'],
                        # models.py 필드명과 일치시킴
                        article_explanation=data['article_explanation'],
                        term_explanation=data['term_explanation'],
                        prediction=data['prediction']
                    )
                    new_explanations.append(expl)
                
                # 저장된 데이터를 뷰에 반영
                explanations = new_explanations
                print("✅ AI 분석 완료 및 DB 저장 성공")
        else:
            print("⚠️ AI 분석 실패 (데이터 없음)")

    # 5. 템플릿에 전달
    context = {
        'article': article,
        'explanations': explanations,
        'user_level': user_level,
    }
    
    return render(request, 'ai_explain.html', context)