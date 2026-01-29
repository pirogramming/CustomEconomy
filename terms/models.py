from django.db import models

class Term(models.Model):
    term_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
