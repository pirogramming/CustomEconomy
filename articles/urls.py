from django.urls import path
from . import views

urlpatterns = [
     path('articleList/', views.articleList_view, name='articleList'),
     path('articleList/bookmark/', views.bookmark_article, name='bookmark_article'),
     path('articleList/unbookmark/', views.unbookmark_article, name='unbookmark_article'),
]