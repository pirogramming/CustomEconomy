from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from articles.models import Article
from accounts.models import Interest, UserInterest
from .models import Quiz, QuizResult, QuizChoice
from .services import get_quiz_session_set
from django.db.models import Count, Q

@login_required
def quiz_view(request, article_id):
    """
    퀴즈 화면: 기사와 관련된 3문제를 생성하거나 가져와서 보여줌
    """
    article = get_object_or_404(Article, id=article_id)
    target_level = request.GET.get('level', 1) # url에서 레벨 가져옴
    quiz_set = get_quiz_session_set(article, target_level=target_level)
    
    # --- 분야 명칭 추출 로직 수정 ---
    sub_categories = article.sub_interests.all()

    if sub_categories.exists():
        # 문자열로 합치지 않고 리스트(객체 묶음) 그대로 전달
        category_display_list = sub_categories 
    elif article.category:
        # 대분류만 있을 경우 리스트 형태로 감싸서 전달 (HTML 반복문을 위해)
        category_display_list = [article.category]
    else:
        category_display_list = []
    return render(request, 'quiz.html', {
        'article': article,
        'quiz_set': quiz_set,
        'category_display_list': category_display_list,
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
            quiz = Quiz.objects.get(id=q_id)
            selected_choice_id = request.POST.get(f'quiz_{q_id}')
            choice = QuizChoice.objects.get(id=selected_choice_id)
            is_correct = choice.is_correct

            # [퀴즈 점수] XP 계산
            earned_xp = 0
            if is_correct:
                correct_count += 1
                if quiz.type in ['A', 'B']:
                    earned_xp = 5
                elif quiz.type == 'C':
                    # 레벨별 XP 매핑
                    level_xp_map = {1: 10, 2: 15, 3: 25, 4: 40, 5: 70}
                    earned_xp = level_xp_map.get(quiz.level, 10)
            
            session_earned_xp += earned_xp

            # QuizResult 저장
            QuizResult.objects.create(
                user=user,
                quiz=quiz,
                selected_answer=choice.choice_text,
                is_correct=is_correct,
                earned_score=earned_xp
            )

            # 결과 데이터 정리
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

            # [약점 점수] Article에 연결된 sub_interests 기준
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

        # [퀴즈 점수] 유저 총점 반영 및 레벨업
        user.total_score += total_final_xp
        
        # [퀴즈 점수] 레벨업 기준 (누적 XP)
        level_thresholds = [(5, 25725), (4, 12985), (3, 5635), (2, 1715)]
        
        old_level = user.level
        new_level = 1
        for lv, xp_needed in level_thresholds:
            if user.total_score >= xp_needed:
                new_level = lv
                break

        is_levelup = new_level > old_level
        if is_levelup:
            user.level = new_level

        next_level_map = {1: 1715, 2: 5635, 3: 12985, 4: 25725, 5: 999999}
        next_xp = next_level_map.get(user.level, 25725)
        remaining_xp = max(0, next_xp - user.total_score)
        
        user.save()

        # 3. 사이드바 연관 기사 추출 (소분류 일치도 기준 정렬)
        sub_categories = article.sub_interests.all()
        related_articles = []
        if sub_categories.exists():
            related_articles = Article.objects.filter(
                sub_interests__in=sub_categories
            ).exclude(id=article.id).distinct().annotate(
                # 현재 기사의 소분류와 몇 개나 겹치는지 카운트
                match_count=Count('sub_interests', filter=Q(sub_interests__in=sub_categories))
            ).order_by('-match_count', '-created_at')[:5]


        
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
            'related_articles': related_articles,         
        })