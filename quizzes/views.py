from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from articles.models import Article
from accounts.models import Interest, UserInterest
from .models import Quiz, QuizResult, QuizChoice
from .services import get_quiz_session_set

@login_required
def quiz_view(request, article_id):
    """
    1. 퀴즈 화면: 기사와 관련된 3문제를 생성하거나 가져와서 보여줌
    """
    article = get_object_or_404(Article, id=article_id)
    quiz_set = get_quiz_session_set(article)
    
    return render(request, 'quiz.html', {
        'article': article,
        'quiz_set': quiz_set
    })

@login_required
@transaction.atomic
def submit_quiz_session(request, article_id):
    """
    2. 퀴즈 제출: 결과 저장 및 약점 점수/날짜 업데이트
    """
    if request.method == "POST":
        user = request.user
        article = get_object_or_404(Article, id=article_id)
        quiz_ids = request.POST.getlist('quiz_ids')
        
        results_detail = []
        correct_count = 0
        
        for q_id in quiz_ids:
            quiz = Quiz.objects.get(id=q_id)
            selected_choice_id = request.POST.get(f'quiz_{q_id}')
            choice = QuizChoice.objects.get(id=selected_choice_id)
            
            is_correct = choice.is_correct
            if is_correct: 
                correct_count += 1

            # [결과 저장] 개별 문제 풀이 기록
            QuizResult.objects.create(
                user=user,
                quiz=quiz,
                selected_answer=choice.choice_text,
                is_correct=is_correct,
                earned_score=10 if is_correct else 0
            )
            
            # [템플릿용 데이터] 결과 페이지에 뿌려줄 정보
            results_detail.append({
                'question': quiz.question,
                'selected': choice.choice_text,
                'is_correct': is_correct,
                'explanation': quiz.explanation,
                'correct_answer': quiz.choices.filter(is_correct=True).first().choice_text
            })

            # [핵심 로직] 약점 점수 및 오답 시각 업데이트
            for cat_name in article.sub_category_names:
                interest_obj, _ = Interest.objects.get_or_create(name=cat_name)
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                
                if is_correct:
                    # 정답인 경우: 약점 점수 2점 차감 (하한 0점은 모델 save에서 처리)
                    ui.weakness_score -= 2
                else:
                    # 오답인 경우: 마지막 오답 시각을 현재로 갱신
                    # 메인 뷰에서 이 시각을 기준으로 3일 내(+4), 7일 내(+2) 가중치 부여
                    ui.last_wrong_at = timezone.now()
                
                ui.save()

        # [유저 성장] 전체 스코어 및 레벨업 로직
        total_session_points = correct_count * 10
        user.total_score += total_session_points
        user.level_score += total_session_points
        
        is_levelup = False
        if user.level_score >= 100:
            user.level += 1
            user.level_score = 0
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
    3. 오답 노트: 유저별 틀린 문제 목록 조회
    """
    wrong_results = QuizResult.objects.filter(
        user=request.user, 
        is_correct=False
    ).select_related('quiz', 'quiz__article').order_by('-created_at')
    
    return render(request, 'wrong_note.html', {
        'wrong_results': wrong_results
    })