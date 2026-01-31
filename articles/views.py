from django.shortcuts import render, HttpResponse
from .models import Article

def articleList_view(request) :
    articles = Article.objects.all().order_by('-created_at')
    
    return render(request, 'articleList.html', {'articles': articles} )