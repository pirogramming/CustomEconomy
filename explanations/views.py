from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from articles.models import Article
from explanations.models import ArticleExplanation
from .utils import GeminiFinancialTutor

# 로그인 기능 구현되면 주석처리 제거
# @login_required
def explanation_detail(request, article_id):
    """
    기사 상세 페이지 및 AI 해설 제공
    """
    # 1. 기사 객체 가져오기 (없으면 404)
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. 해당 기사의 AI 해설이 DB에 존재하는지 확인
    # (이미 분석한 적이 있다면 AI를 또 호출할 필요가 없음 -> 비용/속도 절약)
    explanations = ArticleExplanation.objects.filter(article=article).order_by('level')
    
    
    # 여기부터 로그인기능 없다는 가정하에 테스트용 코드 시작!!
    if request.user.is_authenticated:
        # 로그인 했다면 DB에서 가져오기
        user_interests = list(request.user.interests.values_list('name', flat=True))
        if not user_interests:
            user_interests = ["경제 일반"]
        user_level = request.user.level
    else:
        # 3. 로그인 안 했다면 '테스트용 가짜 데이터' 사용!
        print("📢 비로그인 상태: 테스트용 관심사와 레벨을 사용합니다.")
        user_interests = ["부동산", "주식"]  # 임시 관심사
        user_level = 1                     # 임시 레벨 (1~5 중 선택)
    # 여기까지 테스트용 코드 끝    !!
        
    # 3. 해설이 없다면? -> AI 분석 시작 (최초 1회 실행)
    if not explanations.exists():
        # (1) 사용자 관심사 추출 (UserInterest 모델 활용)
        # 예: ['부동산', '투자']
        user_interests = list(request.user.interests.values_list('name', flat=True))
        if not user_interests:
            user_interests = ["경제 일반"] # 관심사가 없으면 기본값 설정

        # (2) 기사 카테고리 추출 (N:M 관계이므로 첫 번째 것 사용)
        first_category = article.categories.first()
        category_name = first_category.name if first_category else "경제"

        # (3) AI Utils 호출
        tutor = GeminiFinancialTutor()
        print(f"🤖 '{article.title}'에 대한 신규 AI 분석 시작...")
        
        analysis_data = tutor.generate_analysis(
            text=article.content,
            category=category_name,
            interests=user_interests
        )

        # (4) 분석 결과 DB 저장 (Transaction으로 안전하게 처리)
        if analysis_data:
            with transaction.atomic():
                new_explanations = []
                for data in analysis_data:
                    expl = ArticleExplanation(
                        article=article,
                        level=data['level'],
                        article_explanation=data['article_explanation'],
                        term_explanation=data['term_explanation'],
                        prediction=data['prediction']
                    )
                    expl.save()
                    new_explanations.append(expl)
                
                # 저장된 데이터를 변수에 할당하여 바로 템플릿으로 전달
                explanations = new_explanations
        else:
            # AI 분석 실패 시 처리 (예: 에러 메시지 표시)
            print("⚠️ AI 분석 데이터가 비어있습니다.")

    # 4. 사용자의 현재 레벨 가져오기 (기본 탭 활성화용)
    user_level = request.user.level

    context = {
        'article': article,
        'explanations': explanations,
        'user_level': user_level,
    }
    
    # 템플릿 렌더링
    return render(request, 'explanations/detail.html', context)