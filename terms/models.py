from django.db import models
from articles.models import Article

class Term(models.Model):
    name = models.CharField(max_length=50, unique=True)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Article과의 N:M 관계
    articles = models.ManyToManyField(Article, through='ArticleTerm', related_name='terms')

    def __str__(self):
        return self.name

class ArticleTerm(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('article', 'term'),)
