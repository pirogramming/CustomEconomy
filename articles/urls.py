from django.urls import path
from . import views

urlpatterns = [
     path('articleList/', views.articleList_view, name='articleList'),
     path('<int:article_id>/', views.article_detail_view, name='detail'),
]