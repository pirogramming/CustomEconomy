from django.shortcuts import render, get_object_or_404
from .models import Article
from django.core.paginator import Paginator


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
    
    paginator = Paginator(articles_all, 2)
    page_obj = paginator.get_page(page_number)

    context = { 
        'current_category' : category_name,
        'articles' : page_obj,
        'current_sort' : sort
	}
    return render(request, 'articleList.html', context)


def article_detail_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    current_mode = request.GET.get('mode', '기사원문')
    context = {
        'article': article,
        'current_mode': current_mode
    }
    return render(request, 'articleRead.html', context)


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