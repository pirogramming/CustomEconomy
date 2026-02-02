from django.urls import path
from . import views
urlpatterns = [
     path('quiz/<int:article_id>/', views.quiz_view, name='quiz'),
]