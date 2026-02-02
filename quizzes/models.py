from django.db import models
from articles.models import Article, Category
from accounts.models import User

class Quiz(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='quizzes')
    level = models.IntegerField()
    question = models.TextField()
    explanation = models.TextField(help_text="정답 해설")
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class QuizChoice(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=256)
    is_correct = models.BooleanField()

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    attempt_no = models.IntegerField(default=1)
    selected_answer = models.CharField(max_length=50, help_text="객관식 선택값, OX")
    is_correct = models.BooleanField()
    earned_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
