# quizzes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Quiz, QuizChoice, QuizResult
from articles.models import Article

QUIZ_COUNT = 3  # 한 번에 보여줄 문제 수


def quiz_view(request):
    article_id = request.GET.get("article_id") if request.method == "GET" else request.POST.get("article_id")
    level = request.GET.get("level") if request.method == "GET" else request.POST.get("level")
    level = int(level or 1)

    article = None
    if article_id:
        article = get_object_or_404(Article, id=article_id)

    # -------------------------
    # POST: 제출 처리 (⭐ quiz_ids로 동일 세트 유지)
    # -------------------------
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")  # 너희 로그인 url name

        quiz_ids_str = request.POST.get("quiz_ids", "")
        quiz_ids = [int(x) for x in quiz_ids_str.split(",") if x.strip().isdigit()]

        quizzes_list = list(
            Quiz.objects.filter(id__in=quiz_ids).prefetch_related("choices")
        )
        quiz_map = {q.id: q for q in quizzes_list}
        quizzes = [quiz_map[qid] for qid in quiz_ids if qid in quiz_map]

        if not quizzes:
            return render(request, "quiz_empty.html", {"article": article, "level": level})

        total = len(quizzes)
        correct_count = 0
        earned_total_score = 0
        results = []

        for quiz in quizzes:
            picked_choice_id = request.POST.get(f"q_{quiz.id}")

            if not picked_choice_id:
                picked_choice = None
                selected_answer_text = ""
                is_correct = False
                picked_choice_id_int = None
            else:
                picked_choice = QuizChoice.objects.filter(id=picked_choice_id, quiz=quiz).first()
                selected_answer_text = picked_choice.choice_text if picked_choice else ""
                is_correct = bool(picked_choice and picked_choice.is_correct)
                picked_choice_id_int = int(picked_choice_id)

            earned = 10 if is_correct else 0
            if is_correct:
                correct_count += 1
            earned_total_score += earned

            attempt_no = QuizResult.objects.filter(user=request.user, quiz=quiz).count() + 1

            QuizResult.objects.create(
                user=request.user,
                quiz=quiz,
                attempt_no=attempt_no,
                selected_answer=selected_answer_text,
                is_correct=is_correct,
                earned_score=earned,
                created_at=timezone.now(),
            )

            results.append({
                "quiz": quiz,
                "picked_choice_id": picked_choice_id_int,
                "is_correct": is_correct,
                "earned": earned,
            })

        return render(request, "quiz_result.html", {
            "article": article,
            "level": level,
            "results": results,
            "correct_count": correct_count,
            "total": total,
            "earned_total_score": earned_total_score,
        })

    # -------------------------
    # GET: 문제 출제
    # -------------------------
    quizzes_qs = Quiz.objects.none()

    if article:
        quizzes_qs = Quiz.objects.filter(article=article, level=level, type="A")

    if not quizzes_qs.exists():
        if article:
            quizzes_qs = Quiz.objects.filter(category=article.category, type="C")
        else:
            quizzes_qs = Quiz.objects.filter(type="C")

    quizzes = list(quizzes_qs.prefetch_related("choices").order_by("?")[:QUIZ_COUNT])

    if not quizzes:
        return render(request, "quiz_empty.html", {"article": article, "level": level})

    return render(request, "quiz.html", {
        "article": article,
        "level": level,
        "quizzes": quizzes
    })