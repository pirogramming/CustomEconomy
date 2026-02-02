# quizzes/views.py
from django.shortcuts import render, get_object_or_404
from articles.models import Article
from .services import get_quiz_session_set

def quiz_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    # 퀴즈 세트(A, B, C) 가져오기
    quiz_set = get_quiz_session_set(article)
    
    level = request.GET.get('level', 'AI_LV1')
    
    context = {
        'article': article,
        'quiz_set': quiz_set,
        'level': level,
    }
    return render(request, 'quiz.html', context)