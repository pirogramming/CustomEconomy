from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from articles.models import Article
from accounts.models import Interest, UserInterest
from .models import Quiz, QuizResult, QuizChoice
from .services import get_quiz_session_set # 작성하신 함수 임포트

@login_required
def quiz_view(request, article_id):
    """
    1. 기사 상세 페이지 아래에 퀴즈 3문제를 보여주는 뷰
    """
    article = get_object_or_404(Article, id=article_id)
    
    # [Service 호출] A, B, C 유형 섞인 3문제 가져오기
    quiz_set = get_quiz_session_set(article)
    
    return render(request, 'quiz.html', {
        'article': article,
        'quiz_set': quiz_set
    })

@login_required
@transaction.atomic
def submit_quiz_session(request, article_id):
    """
    2. 퀴즈 제출 처리: 점수, 리그, 약점/공백 업데이트
    """
    if request.method == "POST":
        user = request.user
        article = get_object_or_404(Article, id=article_id)
        quiz_ids = request.POST.getlist('quiz_ids')
        
        # 상세 결과를 담을 리스트
        results_detail = []
        correct_count = 0
        
        for q_id in quiz_ids:
            quiz = Quiz.objects.get(id=q_id)
            selected_choice_id = request.POST.get(f'quiz_{q_id}')
            choice = QuizChoice.objects.get(id=selected_choice_id)
            
            is_correct = choice.is_correct
            if is_correct: correct_count += 1

			# [핵심 1] DB에 퀴즈 결과 저장
            QuizResult.objects.create(
                user=user,
                quiz=quiz,
                selected_answer=choice.choice_text,
                is_correct=is_correct,
                earned_score=10 if is_correct else 0
            )
            
            # [상세 정보 저장] 템플릿에서 보여줄 용도
            results_detail.append({
                'question': quiz.question,
                'selected': choice.choice_text,
                'is_correct': is_correct,
                'explanation': quiz.explanation,
                'correct_answer': quiz.choices.filter(is_correct=True).first().choice_text
            })

            # [핵심 2] 약점/공백 점수 업데이트 (추천 엔진용)
            # 기사의 모든 소분류에 대해 점수 가감
            for cat_name in article.sub_category_names:
                interest_obj, _ = Interest.objects.get_or_create(name=cat_name)
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                
                if is_correct:
                    ui.weakness_score = max(0, ui.weakness_score - 2) # 아는 분야
                else:
                    ui.weakness_score += 4 # 약점 분야
                ui.save()

        # [핵심 3] 리그 점수 및 레벨업 로직
        total_session_points = correct_count * 10
        user.total_score += total_session_points
        user.level_score += total_session_points
        
        is_levelup = False
        if user.level_score >= 100: # 레벨업 문턱
            user.level += 1
            user.level_score = 0 # 리그 경쟁용 점수 리셋
            is_levelup = True
        
        user.save()
        
        return render(request, 'session_result.html', {
            'results_detail': results_detail,
            'correct_count': correct_count,
            'is_levelup': is_levelup,
            'points': total_session_points
        })

@login_required
def my_wrong_note(request):
    """
    3. 마이페이지: 틀린 문제 보여주기
    """
    wrong_results = QuizResult.objects.filter(
        user=request.user, 
        is_correct=False
    ).select_related('quiz', 'quiz__article').order_by('-created_at')
    
    return render(request, 'wrong_note.html', {
        'wrong_results': wrong_results
    })