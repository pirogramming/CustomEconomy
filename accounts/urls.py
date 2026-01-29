from django.urls import path
from . import views
urlpatterns = [
     path('mypage/', views.mypage_view, name='mypage'),
     path('login/', views.login_view, name='login'),
     path('signup/', views.signup_view, name='signup'),
     path('league/', views.league_view, name='league'),
]