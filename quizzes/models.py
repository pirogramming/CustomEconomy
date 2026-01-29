from django.db import models

class Quiz(models.Model):
    quiz_id = models.AutoField(primary_key=True)
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
    level = models.IntegerField()
    question = models.TextField()
    type = models.CharField(max_length=20) # 예: MULTIPLE, OX
    created_at = models.DateTimeField(auto_now_add=True)

class QuizChoice(models.Model):
    choice_id = models.AutoField(primary_key=True)
    quiz = models.ForeignKey(Quiz, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=256)
    is_correct = models.BooleanField(default=False)

class QuizAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class QuizResult(models.Model):
    result_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    attempt_no = models.IntegerField(default=1)
    selected_answer = models.CharField(max_length=20)
    is_correct = models.BooleanField()
    earned_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)