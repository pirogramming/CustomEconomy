from django.urls import path
from . import views

urlpatterns = [
     path('<int:article_id>/', views.explanation_detail, name='detail'),
     path('<int:article_id>/generate/<int:level>/', views.generate_level_explanation, name='generate_level'),
]