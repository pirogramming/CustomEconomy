from django.urls import path
from . import views
urlpatterns = [
     path('articleList/', views.articleList_view, name='articleList'),
     path('article/<int:pk>/', views.article_detail_view, name='article_detail'),
]