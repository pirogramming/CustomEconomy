from django.db import models
from accounts.models import User

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_interests = models.ManyToManyField(
        'accounts.Interest',
        related_name='articles',
        blank=True
    )
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True, help_text="미리보기")
    content = models.TextField(help_text="원문")
    image_url = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, unique=True, help_text="기사 중복 방지용")
    source = models.CharField(max_length=50)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_popular = models.BooleanField(default=False)

    # User와의 Bookmark 관계를 ManyToMany로 정의할 수 있습니다.
    bookmarked_by = models.ManyToManyField(User, through='UserBookmark', related_name='bookmarked_articles')

    def __str__(self):
        return self.title
    
    @property
    def sub_category_names(self):
        return self.sub_interests.values_list('name', flat=True)

class UserBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'article'),)
