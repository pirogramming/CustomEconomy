from django.urls import path
from .views import ArticleDetailView

app_name = 'articles'

urlpatterns = [
    path('<int:article_id>/', ArticleDetailView.as_view(), name='article_detail'),
]