from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
     path('mypage/', views.mypage_view, name='mypage'),
     path('signup/', views.signup_view, name='signup'),
     path('login/', views.login_view, name='login'),
     path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
     path('league/', views.league_view, name='league'),
     path('wrongquiz/', views.wrongquiz_view, name='wrongquiz'),
     path('scraparticle/', views.scrap_article_view, name='scraparticle'),
]