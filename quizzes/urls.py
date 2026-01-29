from django.urls import path
from .views import QuizSubmitView

app_name = 'quizzes'

urlpatterns = [
    path('<int:quiz_id>/submit/', QuizSubmitView.as_view(), name='quiz_submit'),
]