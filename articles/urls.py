from django.urls import path
from . import views

urlpatterns = [
     path('articleList/', views.articleList_view, name='articleList'),
]