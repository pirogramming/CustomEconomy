from django.shortcuts import render, get_object_or_404
from .models import Article
from django.core.paginator import Paginator
from django.utils import timezone  # 조회 시각 기록용
from accounts.models import UserInterest, Interest  # 점수 반영용

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
        if article.sub_category_names:
            for cat_name in article.sub_category_names:
                # Interest 테이블에서 name이 같으면서 'SUB(소분류)'인 데이터만 찾습니다.
                # get_or_create 보다는 이미 DB에 18개가 들어있을테니 get을 권장하지만, 
                # 안전하게 가려면 아래처럼 작성하세요.
                interest_obj, _ = Interest.objects.get_or_create(
                    name=cat_name, 
                    defaults={'category_type': 'SUB'} # 새로 만들 때만 SUB로 지정
                )
                
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                
                ui.interest_score += 2
                ui.last_viewed_at = timezone.now()
                ui.save() # 여기서 상한 30점 처리!

    return render(request, 'articles/article_detail.html', {
        'article': article
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