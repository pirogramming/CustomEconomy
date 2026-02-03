from django.shortcuts import render, get_object_or_404
from .models import Article
from django.core.paginator import Paginator
from django.utils import timezone  # 조회 시각 기록용
from accounts.models import UserInterest, Interest  # 점수 반영용
from explanations.models import ArticleExplanation
from explanations.utils import GeminiFinancialTutor
from django.db import transaction

def articleList_view(request):
    sort = request.GET.get('sort', 'newest')
    category_name = request.GET.get('category','경제')
    page_number = request.GET.get('page', '1')
    
    articles_all = Article.objects.filter(category__name=category_name)
    
    if sort == 'newest':
        articles_all = articles_all.order_by('-published_at')
    elif sort == 'oldest':
        articles_all = articles_all.order_by('published_at')
    elif sort == 'title':
        articles_all = articles_all.order_by('title')
    
    paginator = Paginator(articles_all, 9)
    page_obj = paginator.get_page(page_number)

    context = { 
        'current_category' : category_name,
        'articles' : page_obj,
        'current_sort' : sort
	}
    return render(request, 'articleList.html', context)

# 추천을 위한 기사 상세 뷰
def article_detail_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    user = request.user
    
    if user.is_authenticated:
        # 1. 유저 레벨 (마이페이지나 회원정보에 있는 값)
        user_level = getattr(user, 'level', 1) 
        
        # 2. [핵심] 점수 무관! 유저가 초기에 설정/수정한 그 관심사 리스트만 가져오기
        # UserInterest와 연결된 Interest의 'name'들을 리스트로 만듭니다.
        user_interests = list(UserInterest.objects.filter(user=user)
                             .values_list('interest__name', flat=True))
        
        # (만약 가입 때 아무것도 안 골랐을 경우를 대비한 최소한의 장치)
        if not user_interests:
            user_interests = ["소비"]
    else:
        user_level = 1
        user_interests = ["소비"]

    # 1. 유저 점수 로직 (기존 그대로 유지)
    if user.is_authenticated:
        if article.sub_category_names:
            for cat_name in article.sub_category_names:
                interest_obj, _ = Interest.objects.get_or_create(
                    name=cat_name, 
                    defaults={'category_type': 'SUB'}
                )
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                ui.interest_score += 2
                ui.last_viewed_at = timezone.now()
                ui.save()

    # 2. AI 해설 데이터 가져오기 (탭을 채워주기 위해 필요합니다)
    explanations = ArticleExplanation.objects.filter(article=article).order_by('level')

    # 3. 템플릿 렌더링 (ai_explain.html로 연결!)
    if not explanations.exists():
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
                    ArticleExplanation.objects.create(
                        article=article,
                        level=data.get('level', 1),
                        article_explanation=data.get('storytelling', '내용 없음'),
                        term_explanation="\n\n".join([f"📌 {i.get('term')}\n{i.get('explanation')}" for i in data.get('terms', [])]),
                        prediction=data.get('advice', '전망 없음')
                    )
            explanations = ArticleExplanation.objects.filter(article=article).order_by('level')

    # 4. ai_explain.html로 모든 데이터를 실어서 보냅니다!
    return render(request, 'ai_explain.html', {
        'article': article,
        'explanations': explanations,
        'selected_level': 0,
        'user_level': user_level,
    })

# <a href="?category=부동산">부동산</a>
# <option value="?category={{ current_category }}&sort=title" {% if current_sort == 'title' %}selected{% endif %}>이름순</option>
# <p>{{ article.published_at | date:"Y.m.d"}}</p>
# <p>{{ article.category.name }}</p>
# <div class="pagination">
#     {% if articles.has_previous %}
#         <a href="?category={{ current_category }}&sort={{ current_sort }}&page=1">처음으로</a>
#         <a href="?category={{ current_category }}&sort={{ current_sort }}&page={{ articles.previous_page_number }}">이전</a>
#     {% endif %}

#     <span>{{ articles.number }} / {{ articles.paginator.num_pages }}</span>

#     {% if articles.has_next %}
#         <a href="?category={{ current_category }}&sort={{ current_sort }}&page={{ articles.next_page_number }}">다음</a>
#         <a href="?category={{ current_category }}&sort={{ current_sort }}&page={{ articles.paginator.num_pages }}">마지막으로</a>
#     {% endif %}
# </div> 