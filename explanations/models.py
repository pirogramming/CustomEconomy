from django.db import models
from articles.models import Article

class ArticleExplanation(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    level = models.IntegerField(help_text="1~5")
    article_explanation = models.TextField()
    term_explanation = models.TextField()
    prediction = models.TextField()

class InterestBasedPrediction(models.Model):
    """관심사별 전망 캐싱"""
    
    INTEREST_CHOICES = [
        ('대출/금융', '대출/금융'),
        ('부동산', '부동산'),
        ('투자', '투자'),
        ('소비', '소비'),
        ('취업/고용', '취업/고용'),
        ('자영업/사업자', '자영업/사업자'),
        ('세금/정책', '세금/정책'),
        ('환율/해외', '환율/해외'),
    ]
    
    explanation = models.ForeignKey(
        ArticleExplanation, 
        on_delete=models.CASCADE, 
        related_name='interest_predictions'
    )
    interest = models.CharField(max_length=20, choices=INTEREST_CHOICES)
    prediction_text = models.TextField(verbose_name="관심분야 전망")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('explanation', 'interest')
        verbose_name = "관심사별 전망"
    
    def __str__(self):
        return f"{self.explanation.article.title[:20]} Lv{self.explanation.level} - {self.interest}"
