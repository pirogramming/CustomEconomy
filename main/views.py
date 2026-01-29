from django.shortcuts import render
from articles.models import Article

def home(request):
    # 최신 기사 5개를 가져옴
    latest_articles = Article.objects.all().order_by('-created_at')[:5]
    return render(request, 'main/home.html', {'articles': latest_articles})