from django.shortcuts import render
from .models import Article


def articleList_view(request):
    articles = Article.objects.select_related('category').order_by('-published_at')
    
    context = {
        'articles': articles
    }
    
    return render(request, 'articleList.html', context)