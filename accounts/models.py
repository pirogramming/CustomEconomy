from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=40, unique=True)
    password = models.CharField(max_length=256)
    name = models.CharField(max_length=15)
    nickname = models.CharField(max_length=20, unique=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    age = models.IntegerField()
    job = models.CharField(max_length=30)
    level = models.IntegerField(default=1)  # 1~5
    level_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'

class Interest(models.Model):
    interest_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'interest'),)

class UserBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # articles 앱의 Article 참조 (문자열로 참조하여 순환 참조 방지)
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'article'),)