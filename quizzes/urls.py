from django.urls import path
from . import views

urlpatterns = [
     path('<int:article_id>/', views.quiz_view, name='quiz'),
     path('submit/<int:article_id>/', views.submit_quiz_session, name='submit_quiz_session'),
]