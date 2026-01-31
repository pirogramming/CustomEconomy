from django.urls import path
from . import views

app_name = 'explanations'

urlpatterns = [
     path('<int:article_id>/', views.explanation_detail, name='ai_explain'),
]