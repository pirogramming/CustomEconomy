from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
# 👇 [핵심 수정 1] User 모델을 가져오기 위해 꼭 필요합니다!
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm 
from django.contrib.auth.decorators import login_required
from quizzes.models import QuizResult
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect


# 👇 [핵심 수정 2] 현재 활성화된 유저 모델(커스텀 유저)을 가져옵니다.
User = get_user_model()

# 1. 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 1. 로그인할 때 백엔드를 명시해서 한 번에 처리합니다.
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # 2. 로그인 성공 후 바로 리다이렉트!
            return redirect('articleList') 
    else:
        form = CustomUserCreationForm()

    # 아래에 있던 "if user:" 부분은 아예 지워버려야 합니다!
    # 유저가 생성되지 않은 상태(GET 방식 등)에서 실행되면 에러가 나기 때문이죠.
        
    return render(request, 'signup.html', {'form': form})
# 2. 로그인
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('articleList') # 로그인 성공 시 이동할 곳
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 3. 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')

# 4. 마이페이지
def mypage_view(request):
    return render(request, 'mypage.html')

# 5. 리그 페이지 (중복 제거 및 로직 통합 완료)
def league_view(request):
    # 1. URL에 '?level=숫자'가 있는지 확인
    level_param = request.GET.get('level')

    if level_param:
        current_level = int(level_param)
    elif request.user.is_authenticated:
        current_level = request.user.level
    else:
        current_level = 1

    # 2. 해당 레벨의 유저들을 점수 내림차순으로 가져오기 (User 사용 에러 해결됨)
    users = User.objects.filter(level=current_level).order_by('-total_score')[:7]

    # 3. 순위(Rank) 계산 로직
    ranked_users = []
    if users:
        current_rank = 1
        last_score = users[0].total_score
        
        for i, user in enumerate(users):
            if user.total_score < last_score:
                current_rank = i + 1
                last_score = user.total_score
            
            user.rank = current_rank       
            user.rank_position = i + 1     
            ranked_users.append(user)

    # 4. 상위 3명(포디움) vs 나머지 분리
    top_users = ranked_users[:3]
    rest_users = ranked_users[3:]

    context = {
        'current_level': current_level,
        'top_users': top_users,
        'rest_users': rest_users,
    }
    return render(request, 'league.html', context)


@login_required
def wrongquiz_view(request):
    wrong_results = (
        QuizResult.objects
        .filter(user=request.user, is_correct=False)
        .select_related("quiz")
        .prefetch_related("quiz__choices")
        .order_by("-created_at")
    )
    return render(request, "mypage_wrongquiz.html", {"wrong_results": wrong_results})

def scrap_article_view(request):
    return render(request, 'mypage_scraparticle.html')
    
    
    
from .services import (
    load_bank, pick_self_ids, next_question, grade_and_advance, score_to_level
)

SESSION_KEY = "level_test_state"

def _init_state(bank):
    return {
        "phase": "self",
        "self_ids": pick_self_ids(bank),
        "self_idx": 0,
        "current_diff_idx": 0,     # difficulty=1부터
        "asked_ids": [],
        "knowledge_count": 0,
        "total_self": 0.0,
        "total_knowledge": 0.0,
    }

def test_page(request):
    return render(request, "level_test.html")

@require_POST
@csrf_protect
def api_start(request):
    bank = load_bank()
    request.session[SESSION_KEY] = _init_state(bank)
    request.session.modified = True
    return JsonResponse({"ok": True})

@require_GET
def api_next(request):
    bank = load_bank()
    state = request.session.get(SESSION_KEY)

    if not state:
        return JsonResponse({"error": "not_started"}, status=400)

    if state["phase"] == "done":
        total = float(state["total_self"]) + float(state["total_knowledge"])
        level = score_to_level(total)
        return JsonResponse({"done": True, "total": total, "level": level})

    q = next_question(bank, state)
    if not q:
        # 안전 처리
        state["phase"] = "done"
        request.session[SESSION_KEY] = state
        request.session.modified = True
        total = float(state["total_self"]) + float(state["total_knowledge"])
        level = score_to_level(total)
        return JsonResponse({"done": True, "total": total, "level": level})

    # 프론트에 필요한 최소 정보만 내려줌
    payload = {
        "done": False,
        "qid": q["id"],
        "type": q["type"],
        "difficulty": q.get("difficulty", 0),
        "question": q["question"],
        "options": [opt["text"] for opt in q["options"]],
        "progress": {
            "phase": state["phase"],
            "self": {"current": state["self_idx"] + 1, "total": 2} if state["phase"] == "self" else None,
            "knowledge": {"current": state["knowledge_count"] + 1, "total": 5} if state["phase"] == "knowledge" else None,
        }
    }
    return JsonResponse(payload)

@require_POST
@csrf_protect
def api_submit(request):
    bank = load_bank()
    state = request.session.get(SESSION_KEY)
    if not state:
        return JsonResponse({"error": "not_started"}, status=400)

    qid = request.POST.get("qid")
    picked = request.POST.get("picked")  # "0"~"3"
    if qid is None or picked is None:
        return JsonResponse({"error": "bad_request"}, status=400)

    try:
        picked_index = int(picked)
    except:
        return JsonResponse({"error": "bad_pick"}, status=400)

    state, result = grade_and_advance(bank, state, qid, picked_index)
    request.session[SESSION_KEY] = state
    request.session.modified = True

    done = (state["phase"] == "done")
    if done:
        total = float(state["total_self"]) + float(state["total_knowledge"])
        level = score_to_level(total)
        result.update({"done": True, "total": total, "level": level})
    else:
        result.update({"done": False})

    return JsonResponse(result)

def result_page(request):
    state = request.session.get(SESSION_KEY)
    if not state:
        return redirect("level_test:page")

    total = float(state["total_self"]) + float(state["total_knowledge"])
    level = score_to_level(total)

    # (선택) 로그인 유저면 레벨 저장하고 싶을 때:
    if request.user.is_authenticated:
        # 너희 User 모델에 level 필드 있으니 필요하면 활성화
        request.user.level = level
        request.user.save(update_fields=["level"])

    return render(request, "level_test_result.html", {
        "total_self": state["total_self"],
        "total_knowledge": state["total_knowledge"],
        "total": total,
        "level": level,
    })