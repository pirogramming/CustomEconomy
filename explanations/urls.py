from django.urls import path
from .views import ExplanationView

app_name = 'explanations'

urlpatterns = [
    path('article/<int:article_id>/', ExplanationView.as_view(), name='explanation_detail'),
]