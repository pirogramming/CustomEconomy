from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, nickname, email=None, password=None, **extra_fields):
        if not nickname:
            raise ValueError('닉네임(ID)은 필수입니다')
        
        email = self.normalize_email(email)
        user = self.model(nickname=nickname, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nickname, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(nickname, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    nickname = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=40, unique=True)
    name = models.CharField(max_length=15)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    age = models.IntegerField(default=20)
    job = models.CharField(max_length=30, default="unknown")
    level = models.IntegerField(default=1, help_text="1~5")
    level_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'nickname' 

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
