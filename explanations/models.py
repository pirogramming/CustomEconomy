from django.db import models

class ArticleExplanation(models.Model):
    explanation_id = models.AutoField(primary_key=True)
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
    level = models.IntegerField()  # 1~5
    background_text = models.TextField()
    detail_text = models.TextField()