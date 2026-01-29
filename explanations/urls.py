from django.urls import path
from . import views
urlpatterns = [
     path('ai_explain/', views.ai_explain_view, name='ai_explain'),
]