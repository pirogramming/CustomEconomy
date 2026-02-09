import json
from django.shortcuts import render, get_object_or_404
from .models import Article, UserBookmark
from django.core.paginator import Paginator
from django.utils import timezone  # 조회 시각 기록용
from accounts.models import UserInterest, Interest  # 점수 반영용
from explanations.models import ArticleExplanation
from explanations.utils import GeminiFinancialTutor
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

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


@login_required
@require_POST
def bookmark_article(request):
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        payload = {}

    article_id = payload.get('article_id')
    if not article_id:
        return JsonResponse({'ok': False, 'error': 'no_id'}, status=400)

    article = get_object_or_404(Article, id=article_id)
    obj, created = UserBookmark.objects.get_or_create(user=request.user, article=article)

    # 전체 북마크 리스트 반환 (기존 방식 유지)
    qs = UserBookmark.objects.filter(user=request.user).order_by('-created_at').select_related('article')
    data = [
        {
            'id': b.article.id,
            'title': b.article.title,
            'image_url': b.article.image_url,
            'source': b.article.source,
            'url': b.article.url,
            'published_at': b.article.published_at.isoformat() if b.article.published_at else None,
        }
        for b in qs
    ]
    return JsonResponse({'ok': True, 'created': created, 'bookmarks': data})

@login_required
@require_POST
def unbookmark_article(request):
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        payload = {}

    article_id = payload.get('article_id')
    deleted_count, _ = UserBookmark.objects.filter(user=request.user, article_id=article_id).delete()

    qs = UserBookmark.objects.filter(user=request.user).order_by('-created_at').select_related('article')
    data = [
        {
            'id': b.article.id,
            'title': b.article.title,
            'image_url': b.article.image_url,
            'source': b.article.source,
            'url': b.article.url,
            'published_at': b.article.published_at.isoformat() if b.article.published_at else None,
        }
        for b in qs
    ]
    return JsonResponse({'ok': True, 'deleted': deleted_count > 0, 'bookmarks': data})