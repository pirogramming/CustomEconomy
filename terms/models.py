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


class TermBookmark(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='term_bookmarks')
    word = models.CharField(max_length=100)
    definition = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'word'),)

    def __str__(self):
        return f"{self.user.email} - {self.word}"
