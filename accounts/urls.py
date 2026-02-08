from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
     path('mypage/', views.mypage_view, name='mypage'),
     path('signup/', views.signup_view, name='signup'),
     path('login/', views.login_view, name='login'),
     path('logout/', views.logout_view, name='logout'),
     path('league/', views.league_view, name='league'),
     path('wrongquiz/', views.wrongquiz_view, name='wrongquiz'),
     path('scraparticle/', views.scrap_article_view, name='scraparticle'),
     path('level_test/', views.test_page, name='level_test'),
     path("level_test/start/", views.api_start, name="level_test_start"),  # 세션 초기화
     path("level_test/next/", views.api_next, name="level_test_next"),     # 다음 문제 가져오기
     path("level_test/submit/", views.api_submit, name="level_test_submit"), # 답 제출(채점/다음)
     path("level_test/result/", views.result_page, name="level_test_result"),      # 결과 화면
]