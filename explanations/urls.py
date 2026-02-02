from django.urls import path
from . import views

urlpatterns = [
     path('<int:article_id>/', views.explanation_detail, name='detail'),
]