from django.db import models
from articles.models import Article, Category
from accounts.models import User

class Quiz(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quizzes',
        help_text="5개 대분류 (기사 카테고리-C유형 소분류 없는 경우)"
    )
    interest = models.ForeignKey(
        'accounts.Interest', 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        null=True,
        blank=True,
        help_text="18개 소분류 (약점 분석용)"
    )
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
    selected_answer = models.TextField()
    is_correct = models.BooleanField()
    earned_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
