from django.db import models

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)

class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    content = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, unique=True)
    source = models.CharField(max_length=50)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # terms 앱과의 다대다 관계는 ArticleTerm 테이블 대신 ManyToManyField로 처리 가능
    terms = models.ManyToManyField('terms.Term', related_name='articles')