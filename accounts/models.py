from django.db import models
from django.contrib.auth.models import AbstractBaseUser # 커스텀 유저 사용 시

class User(models.Model):
    email = models.EmailField(max_length=40, unique=True)
    password = models.CharField(max_length=256)
    name = models.CharField(max_length=15)
    nickname = models.CharField(max_length=20, unique=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    age = models.IntegerField()
    job = models.CharField(max_length=30)
    level = models.IntegerField(help_text="1~5")
    level_score = models.IntegerField()
    total_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nickname

class Interest(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    score = models.IntegerField()
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'interest'),)