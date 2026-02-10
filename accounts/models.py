from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다')

        email = self.normalize_email(email)
        # prefer provided username, otherwise derive from email local-part
        username = extra_fields.pop('username', None)
        if not username:
            username = email.split('@')[0]

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username= models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=40, unique=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    level = models.IntegerField(default=1, help_text="1~5")
    level_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
    
class Interest(models.Model):
    # '관심분야(MAIN)' 또는 '소분류(SUB)'
    TYPE_CHOICES = [
        ('MAIN', '8개 관심분야'),
        ('SUB', '18개 소분류'),
    ]
    
    name = models.CharField(max_length=30, unique=True)
    category_type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        default='MAIN'
    )

    def __str__(self):
        return f"[{self.get_category_type_display()}] {self.name}"

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    
    # [MAIN 전용] 유저 가입 시 선택 여부
    is_selected = models.BooleanField(default=False, help_text="유저가 직접 선택한 관심사 여부")
    
    # [SUB 전용] 학습/조회 점수
    interest_score = models.IntegerField(default=0, help_text="관심 점수 (상한 30점)")
    weakness_score = models.IntegerField(default=0, help_text="약점/공백 점수 (하한 0점)")
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    last_wrong_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'interest'),)

    def save(self, *args, **kwargs):
        # 1. 관심 점수: 0 ~ 30점 사이로 고정
        if self.interest_score > 30:
            self.interest_score = 30
        elif self.interest_score < 0:
            self.interest_score = 0
            
        # 2. 약점 점수: 최소 0점 보장
        if self.weakness_score < 0:
            self.weakness_score = 0
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.interest.name} (I:{self.interest_score}, W:{self.weakness_score})"