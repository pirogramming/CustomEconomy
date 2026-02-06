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
    
    # --- 분야 명칭 추출 로직 추가 ---
    # 1. 소분류(sub_interests)가 있는지 확인
    sub_categories = article.sub_interests.all()
    
    if sub_categories.exists():
        # 소분류가 있으면 소분류 이름들을 쉼표로 연결
        category_display = ", ".join([sc.name for sc in sub_categories])
    elif article.category:
        # 소분류가 없고 대분류(category)만 있으면 대분류 이름 사용
        category_display = article.category.name
    else:
        # 소분류, 대분류 모두 없을 경우를 대비한 기본값
        category_display = "경제 일반"

    return render(request, 'quiz.html', {
        'article': article,
        'quiz_set': quiz_set,
        'category_display': category_display,
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
            
            # 1. 답 선택 여부 확인
            if selected_choice_id:
                choice = QuizChoice.objects.get(id=selected_choice_id)
                is_correct = choice.is_correct
                selected_text = choice.choice_text # 실제 선택한 텍스트
            else:
                is_correct = False
                selected_text = "(미선택)" # 선택 안 했을 때의 텍스트

            if is_correct: 
                correct_count += 1

            # [결과 저장] 개별 문제 풀이 기록
            QuizResult.objects.create(
                user=user,
                quiz=quiz,
                selected_answer=selected_text,
                is_correct=is_correct,
                earned_score=10 if is_correct else 0
            )
            
            # 선택한 choice id (템플릿에서 빨강 표시용)
            selected_choice_id_int = int(selected_choice_id) if selected_choice_id else None

            # 정답 choice
            correct_choice = quiz.choices.filter(is_correct=True).first()
            correct_choice_id = correct_choice.id if correct_choice else None
            correct_choice_text = correct_choice.choice_text if correct_choice else "(정답 없음)"

            # 선지 전체 (id + text)
            all_choices = list(quiz.choices.all().values("id", "choice_text"))

            results_detail.append({
                "quiz_id": quiz.id,
                "question": quiz.question,
                "selected": selected_text,
                "selected_choice_id": selected_choice_id_int,
                "is_correct": is_correct,
                "explanation": quiz.explanation,
                "correct_answer": correct_choice_text,
                "correct_choice_id": correct_choice_id,
                "choices": all_choices,  # ✅ 전체 보기용
            })


            # [핵심 로직] 기사에 연결된 모든 소분류(Interest)에 대해 점수 반영
            article_interests = article.sub_interests.all() 
            
            for interest_obj in article_interests:
                # get_or_create로 유저의 관심사 기록이 없으면 생성
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                
                if is_correct:
                    # 정답인 경우: 약점 점수 2점 차감 (하한 0점은 모델 save에서 처리)
                    ui.weakness_score -= 2
                else:
                    # 오답인 경우: 약점 점수 2점 증가
                    # 오답인 경우: 마지막 오답 시각을 현재로 갱신
                    # 메인 뷰에서 이 시각을 기준으로 3일 내(+4), 7일 내(+2) 가중치 부여
                    ui.weakness_score += 2
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
        
        return render(request, 'quiz_result.html', {
            'results_detail': results_detail,
            'correct_count': correct_count,
            'is_levelup': is_levelup,
            'points': total_session_points,
            'article': article,         
        })

# 미완성 (틀린 문제 확인하기)
@login_required
def my_wrong_note(request):
    """
    3. 오답 노트: 유저별 틀린 문제 목록 조회
    """
    wrong_results = QuizResult.objects.filter(
        user=request.user, 
        is_correct=False
    ).select_related('quiz', 'quiz__article').prefetch_related('quiz__choices').order_by('-created_at')
    
    return render(request, 'wrong_note.html', {
        'wrong_results': wrong_results
    })