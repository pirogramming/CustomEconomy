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
from .models import Interest, UserInterest
from django.db import transaction
from django.contrib import messages
from pathlib import Path


User = get_user_model()

# 아래 transaction.atomic가 뭐냐면 유저 생성과 유저의 관심분야 저장을 한 작업으로 묶는 것임
# 계정은 생성되었는데 관심분야 저장에 실패하면 DB 꼬임. 이런 상황을 막음
# 하나가 실패하면 전체 rollback
@transaction.atomic 
def signup_view(request):
    if request.method == "GET":
        return render(request, "signup.html")

    email = request.POST.get("email", "").strip()
    name = request.POST.get("name", "").strip()
    password = request.POST.get("password", "")
    password_confirm = request.POST.get("password_confirm", "")

    raw = request.POST.get("selected_interests", "")
    selected_names = [s.strip() for s in raw.split(",") if s.strip()]

    # --- 서버 검증 ---
    if not email:
        messages.error(request, "이메일을 입력해 주세요.")
        return redirect("signup")

    if password != password_confirm:
        messages.error(request, "비밀번호가 일치하지 않습니다.")
        return redirect("signup")

    if len(password) < 8:
        messages.error(request, "비밀번호는 8자 이상이어야 합니다.")
        return redirect("signup")

    if User.objects.filter(email=email).exists():
        messages.error(request, "이미 사용 중인 이메일입니다.")
        return redirect("signup")

    if not selected_names:
        messages.error(request, "관심분야를 최소 1개 선택해 주세요.")
        return redirect("signup")
    


    # --- 유저 생성 (nickname은 manager에서 자동 생성되는 구조라고 가정) ---
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name
    )

    # --- 관심사 저장 (MAIN 8개 중 선택된 것만 is_selected=True) ---
    interests = list(Interest.objects.filter(category_type="MAIN", name__in=selected_names))
    
    print("selected_names:", selected_names)  # ← 여기 OK
    print("matched interests:", [i.name for i in interests])  # ⭐ 여기!

    # 프론트에서 이상한 값이 오면 방어
    if len(interests) != len(set(selected_names)):
        messages.error(request, "유효하지 않은 관심분야가 포함되어 있습니다.")
        raise ValueError("Invalid interest names")

    UserInterest.objects.bulk_create([
        UserInterest(user=user, interest=i, is_selected=True)
        for i in interests
    ])

    # --- 가입 후 자동 로그인 ---
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("articleList")

# 2. 로그인
def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")

    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")

    # ⭐ 핵심: authenticate는 인자명이 username임
    user = authenticate(request, username=email, password=password)

    if user is None:
        messages.error(request, "이메일 또는 비밀번호가 올바르지 않습니다.")
        return redirect("login")

    login(request, user)
    return redirect("articleList")

# 3. 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')

# 4. 마이페이지
def mypage_view(request):
    context = {}
    if request.user.is_authenticated:
        # MAIN 관심분야 중 사용자가 선택한 것들
        selected = list(
            UserInterest.objects.filter(
                user=request.user,
                interest__category_type='MAIN',
                is_selected=True
            ).values_list('interest__name', flat=True)
        )
        context['user_selected_interests'] = selected
        context['user_nickname'] = request.user.nickname
        context['user_image_url'] = request.user.image_url
        # session-stored term bookmarks (if any)
        context['term_bookmarks'] = request.session.get('term_bookmarks', [])

    return render(request, 'mypage.html', context)

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

@login_required
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

@login_required
def edit_view(request):
    # 전달할 관심분야 목록 (MAIN 8개) 및 사용자가 선택한 항목
    main_interests = list(Interest.objects.filter(category_type='MAIN').values_list('name', flat=True))
    user_selected = set(
        UserInterest.objects.filter(user=request.user, interest__category_type='MAIN', is_selected=True)
        .values_list('interest__name', flat=True)
    )

    return render(request, 'mypage_edit.html', {
        'main_interests': main_interests,
        'user_selected_interests': user_selected,
    })


@login_required
@require_POST
def update_nickname(request):
    new_nick = request.POST.get('nickname', '').strip()
    if not new_nick:
        messages.error(request, '닉네임을 입력해 주세요.')
        return redirect('edit')

    if len(new_nick) > 20:
        messages.error(request, '닉네임은 20자 이내여야 합니다.')
        return redirect('edit')

    if User.objects.exclude(pk=request.user.pk).filter(nickname=new_nick).exists():
        messages.error(request, '이미 사용 중인 닉네임입니다.')
        return redirect('edit')

    request.user.nickname = new_nick
    request.user.save(update_fields=['nickname'])
    messages.success(request, '닉네임이 변경되었습니다.')
    return redirect('edit')


@login_required
@require_POST
def update_interest(request):
    # 선택 체크박스는 name='interests'로 여러값 전송
    selected = request.POST.getlist('interests')

    # DB에 있는 MAIN 관심사만 허용
    valid = list(Interest.objects.filter(category_type='MAIN', name__in=selected))

    with transaction.atomic():
        # 기존 MAIN 관계 제거
        UserInterest.objects.filter(user=request.user, interest__category_type='MAIN').delete()

        # 선택된 항목 생성
        UserInterest.objects.bulk_create([
            UserInterest(user=request.user, interest=i, is_selected=True)
            for i in valid
        ])

    messages.success(request, '관심분야가 저장되었습니다.')
    return redirect('edit')


@login_required
@require_POST
def update_photo(request):
    # 파일을 프로젝트 static/img/uploads 에 저장하고 URL을 user.image_url에 저장
    from django.conf import settings

    # 리셋 요청 처리
    if request.POST.get('reset_default') == '1':
        request.user.image_url = None
        request.user.save(update_fields=['image_url'])
        messages.success(request, '기본 프로필로 변경되었습니다.')
        return redirect('edit')

    file = request.FILES.get('photo')
    if not file:
        messages.error(request, '업로드할 파일을 선택해 주세요.')
        return redirect('edit')

    upload_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 안전한 파일명
    import uuid
    ext = Path(file.name).suffix
    fname = f"user_{request.user.id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = upload_dir / fname

    with open(dest, 'wb') as out:
        for chunk in file.chunks():
            out.write(chunk)

    # 개발환경에서 접근 가능한 static 경로로 저장
    request.user.image_url = settings.STATIC_URL + f"img/uploads/{fname}"
    request.user.save(update_fields=['image_url'])
    messages.success(request, '프로필 사진이 변경되었습니다.')
    return redirect('edit')
    

@login_required
def scrap_term_view(request):
    return render(request, 'mypage_scrapterm.html')
