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
    퀴즈 화면: 기사와 관련된 3문제를 생성하거나 가져와서 보여줌
    """
    article = get_object_or_404(Article, id=article_id)
    target_level = request.GET.get('level', 1) # url에서 레벨 가져옴
    quiz_set = get_quiz_session_set(article, target_level=target_level)
    
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
    퀴즈 제출: 결과 저장 및 약점 점수/날짜 업데이트
    """
    if request.method == "POST":
        user = request.user
        article = get_object_or_404(Article, id=article_id)
        quiz_ids = request.POST.getlist('quiz_ids')
        
        results_detail = []
        correct_count = 0
        session_earned_xp = 0 

        for q_id in quiz_ids:
            # ... (이 부분은 기존과 동일하므로 생략, 그대로 두세요) ...
            quiz = Quiz.objects.get(id=q_id)
            selected_choice_id = request.POST.get(f'quiz_{q_id}')
            choice = QuizChoice.objects.get(id=selected_choice_id)
            is_correct = choice.is_correct

            earned_xp = 0
            if is_correct:
                correct_count += 1
                if quiz.type in ['A', 'B']:
                    earned_xp = 5
                elif quiz.type == 'C':
                    level_xp_map = {1: 10, 2: 15, 3: 25, 4: 40, 5: 70}
                    earned_xp = level_xp_map.get(quiz.level, 10)
            
            session_earned_xp += earned_xp

            QuizResult.objects.create(
                user=user,
                quiz=quiz,
                selected_answer=choice.choice_text,
                is_correct=is_correct,
                earned_score=earned_xp
            )

            correct_choice = quiz.choices.filter(is_correct=True).first()
            results_detail.append({
                "quiz_id": quiz.id,
                "quiz_type": quiz.type,
                "question": quiz.question,
                "selected": choice.choice_text,
                "is_correct": is_correct,
                "explanation": quiz.explanation,
                "correct_answer": correct_choice.choice_text if correct_choice else "(정답 없음)",
                "choices": list(quiz.choices.all().values("id", "choice_text")),
                "earned_xp": earned_xp,
            })

            # 약점 점수 로직 (기존 유지)
            article_interests = article.sub_interests.all() 
            for interest_obj in article_interests:
                ui, _ = UserInterest.objects.get_or_create(user=user, interest=interest_obj)
                if is_correct:
                    ui.weakness_score -= 2
                else:
                    ui.weakness_score += 2
                    ui.last_wrong_at = timezone.now()
                ui.save()

        # [퀴즈 점수] 세트 보너스
        bonus_xp = 5 if correct_count == 2 else (15 if correct_count == 3 else 0)
        total_final_xp = session_earned_xp + bonus_xp

        # 🔥🔥🔥 [핵심 수정] 점수 보정 로직 시작 🔥🔥🔥
        # 형님의 현재 레벨에 맞는 최소 점수를 확인합니다.
        min_xp_map = {1: 0, 2: 1715, 3: 5635, 4: 12985, 5: 25725}
        current_min_xp = min_xp_map.get(user.level, 0)
        
        # 만약 현재 점수가 레벨 시작점보다 낮다면(좀비 데이터), 강제로 시작점으로 맞춥니다.
        if user.total_score < current_min_xp:
            user.total_score = current_min_xp

        # 그 다음 획득한 경험치를 더합니다.
        user.total_score += total_final_xp
        # 🔥🔥🔥 [핵심 수정] 끝 🔥🔥🔥
        
        # [퀴즈 점수] 레벨업 기준 (누적 XP)
        level_thresholds = [(5, 25725), (4, 12985), (3, 5635), (2, 1715)]
        
        old_level = user.level
        new_level = 1 # 기본값
        
        # 현재 점수에 맞춰 레벨 재계산 (레벨 다운 방지 로직 필요시 old_level과 비교)
        for lv, xp_needed in level_thresholds:
            if user.total_score >= xp_needed:
                new_level = lv
                break
        
        # 레벨은 오르기만 하고 떨어지진 않게 하려면 max 사용
        new_level = max(new_level, old_level)

        is_levelup = new_level > old_level
        if is_levelup:
            user.level = new_level

        next_level_map = {1: 1715, 2: 5635, 3: 12985, 4: 25725, 5: 999999}
        next_xp = next_level_map.get(user.level, 25725)
        # 음수 방지
        remaining_xp = max(0, next_xp - user.total_score)
        
        user.save()
        
        return render(request, 'quiz_result.html', {
            'results_detail': results_detail,
            'correct_count': correct_count,
            'is_levelup': is_levelup,
            'base_xp': session_earned_xp,
            'xp_breakdown': {
                'type_a': sum(r['earned_xp'] for r in results_detail if r['quiz_type'] == 'A'),
                'type_b': sum(r['earned_xp'] for r in results_detail if r['quiz_type'] == 'B'),
                'type_c': sum(r['earned_xp'] for r in results_detail if r['quiz_type'] == 'C'),
            },
            'bonus_xp': bonus_xp,
            'total_final_xp': total_final_xp,
            'current_total_xp': user.total_score,
            'remaining_xp': remaining_xp,
            'article': article,         
        })