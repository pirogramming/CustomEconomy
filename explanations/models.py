from django.db import models
from articles.models import Article

class ArticleExplanation(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    level = models.IntegerField(help_text="1~5")
    article_explanation = models.TextField()
    term_explanation = models.TextField()
    prediction = models.TextField()