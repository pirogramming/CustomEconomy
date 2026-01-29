from django.shortcuts import render
from articles.models import Article

def home(request):
    # 여러 앱의 데이터를 한 화면에 모을 수 있음
    latest_articles = Article.objects.all().order_by('-created_at')[:5]
    # 필요하다면 여기서 인기도 높은 용어(Terms)나 퀴즈도 가져올 수 있음
    return render(request, 'main/home.html', {'articles': latest_articles})