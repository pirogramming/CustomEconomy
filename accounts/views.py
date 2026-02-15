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
import logging
logger = logging.getLogger(__name__)


User = get_user_model()

# 아래 transaction.atomic가 뭐냐면 유저 생성과 유저의 관심분야 저장을 한 작업으로 묶는 것임
# 계정은 생성되었는데 관심분야 저장에 실패하면 DB 꼬임. 이런 상황을 막음
# 하나가 실패하면 전체 rollback
@transaction.atomic 
def signup_view(request):
    if request.method == "GET":
        return render(request, "signup.html")

    # 1. 데이터 가져오기
    email = request.POST.get("email", "").strip()
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    password_confirm = request.POST.get("password_confirm", "")
    raw = request.POST.get("selected_interests", "")
    selected_names = [s.strip() for s in raw.split(",") if s.strip()]

    # 입력값 유지 및 에러 전달을 위한 기본 context
    ctx = {
        'email': email,
        'username': username,
        'selected_interests': selected_names, # 기존 선택한 관심사 유지용
    }

    # 에러 여부를 판단할 플래그
    has_error = False

    # --- 서버 검증 (이제 팝업 대신 주황색 글씨로 뜹니다) ---

    # 1. 이메일 체크
    if not email:
        ctx['email_error'] = "이메일을 입력해 주세요."
        has_error = True
    elif User.objects.filter(email=email).exists():
        from allauth.socialaccount.models import SocialAccount
        existing_user = User.objects.get(email=email)
        if SocialAccount.objects.filter(user=existing_user).exists():
            providers = list(SocialAccount.objects.filter(user=existing_user).values_list('provider', flat=True))
            ctx.update({'email_error': '이미 소셜 로그인으로 등록된 이메일입니다.', 'social_providers': providers})
        else:
            ctx['email_error'] = "이미 사용 중인 이메일입니다."
        has_error = True

    # 2. 사용자 이름(닉네임) 체크
    if not username:
        ctx['username_error'] = "사용하실 이름을 입력해 주세요."
        has_error = True
    elif User.objects.filter(username=username).exists():
        ctx['username_error'] = "이미 사용 중인 이름입니다."
        has_error = True

    # 3. 비밀번호 일치 및 길이 체크
    if password != password_confirm:
        ctx['password_confirm_error'] = "비밀번호가 일치하지 않습니다."
        has_error = True
    
    if len(password) < 8:
        ctx['password_error'] = "비밀번호는 8자 이상이어야 합니다."
        has_error = True

    # 4. 관심분야 체크
    if not selected_names:
        ctx['selected_interests_error'] = "관심분야를 최소 1개 선택해 주세요."
        has_error = True

    # 만약 하나라도 에러가 있다면, 회원가입 페이지로 다시 렌더링 (ctx에 담긴 에러메시지들과 함께)
    if has_error:
        return render(request, 'signup.html', ctx)

    # --- 모든 검증 통과 시 유저 생성 ---
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            username=username
        )

        # 관심사 저장 로직
        interests = list(Interest.objects.filter(category_type="MAIN", name__in=selected_names))
        UserInterest.objects.bulk_create([
            UserInterest(user=user, interest=i, is_selected=True)
            for i in interests
        ])

        # 로그인 처리
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        
        # 가입 성공 시 메인 페이지로 이동하면서 성공 데이터 전달
        return render(request, "main.html", {
            "signup_success": True,
            "user_name": user.username,
        })
        
    except Exception as e:
        logger.exception("Signup failed")  # ✅ EB 로그에 스택트레이스 남김

        # 화면에 원인까지 노출(디버깅용)
        ctx["form_error"] = f"{type(e).__name__}: {e}"

        return render(request, "signup.html", ctx)

    


def signup_popup(request):
    return render(request, "level_test_popup.html")


# 2. 로그인
def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")
    # accept email input for login (with fallback)
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")

    # Try authenticating via email (allauth backend) first
    user = authenticate(request, email=email, password=password)
    if user is None:
        # fallback: try authenticating using username field
        user = authenticate(request, username=email, password=password)

    if user is None:
        # Determine whether the failure is due to unknown email/username, wrong password,
        # or the account being social-only (no usable password)
        user_obj = None
        if email:
            user_obj = User.objects.filter(email=email).first()
        if not user_obj:
            user_obj = User.objects.filter(username=email).first()

        if user_obj:
            # If the user has no usable password (social-only), treat as unregistered for password login
            if not user_obj.has_usable_password():
                # find which social providers are linked for this user
                from allauth.socialaccount.models import SocialAccount
                providers = list(SocialAccount.objects.filter(user=user_obj).values_list('provider', flat=True))
                context = {
                    'email_error': '가입되지 않은 이메일입니다. 소셜 로그인을 사용해 주세요.',
                    'email': email,
                    'social_providers': providers,
                }
                return render(request, 'login.html', context)

            # account exists and has a password -> password issue
            context = {
                'password_error': '비밀번호가 올바르지 않습니다.',
                'email': email,
            }
            return render(request, 'login.html', context)

        # no such account at all
        context = {
            'email_error': '등록된 이메일 또는 사용자 이름이 없습니다.',
            'email': email,
        }
        return render(request, 'login.html', context)

    login(request, user)
    return redirect("articleList")

# 3. 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')

# 4. 마이페이지
@login_required
def mypage_view(request):
    progress_percent = 0
    points_to_next_level = 0
    # 1. 레벨 데이터 및 변수 정의
    next_level_map = {1: 1715, 2: 5635, 3: 12985, 4: 25725, 5: 999999}
    prev_level_map = {1: 0, 2: 1715, 3: 5635, 4: 12985, 5: 25725}
    
    current_level = int(request.user.level)
    current_total_score = float(request.user.total_score if request.user.total_score else 0)
    
    next_xp = float(next_level_map.get(current_level, 999999))
    prev_xp = float(prev_level_map.get(current_level, 0))

    # 2. 퍼센트 계산
    if current_level >= 5:
        points_to_next_level = 0
        progress_percent = 100
    else:
        points_to_next_level = max(0, int(next_xp - current_total_score))
        level_range = next_xp - prev_xp
        current_progress = max(0, current_total_score - prev_xp)
        
        if level_range > 0:
            raw_percent = (float(current_progress) / float(level_range)) * 100
            progress_percent = min(100, int(raw_percent))
        else:
            progress_percent = 0

    print(f"🔥🔥 Progress Calculation 🔥🔥")
    print(f"  Progress Percent: {progress_percent}%")
    print(f"  Points to Next: {points_to_next_level}")
   
    # 3. 관심분야
    selected = list(
        UserInterest.objects.filter(
            user=request.user,
            interest__category_type='MAIN',
            is_selected=True
        ).values_list('interest__name', flat=True)
    )
    
    # 4. 뉴스 스크랩
    try:
        articles_qs = request.user.bookmarked_articles.select_related('category').prefetch_related('sub_interests').order_by('?')[:3]
        preview_list = []
        for art in articles_qs:
            preview_list.append({
                'id': art.id,
                'title': art.title,
                'image_url': art.image_url,
                'category': getattr(art.category, 'name', ''),
                'sub_categories': list(art.sub_interests.values_list('name', flat=True)),
            })
        article_bookmarks_preview = preview_list
    except:
        article_bookmarks_preview = []

    # 5. 오답노트
    wrong_results = QuizResult.objects.filter(
        user=request.user, is_correct=False
    ).select_related("quiz").order_by("-created_at")[:10]
    
    # 🔥 마지막에 한 번에 context 생성!
    context = {
        'user_selected_interests': selected,
        'user_nickname': request.user.username,
        'user_image_url': request.user.image_url,
        'term_bookmarks': request.session.get('term_bookmarks', []),
        'points_to_next_level': points_to_next_level,
        'progress_percent': progress_percent,
        'article_bookmarks_preview': article_bookmarks_preview,
        'wrong_results': wrong_results,
    }
    
    # 🔥 최종 디버깅
    print(f"🔥🔥 FINAL CONTEXT 🔥🔥")
    print(f"  progress_percent in context: {context['progress_percent']}")
    
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
    # include user's article bookmarks for initial render
    from articles.models import UserBookmark
    bookmarks = []
    if request.user.is_authenticated:
        qs = (
            UserBookmark.objects
            .filter(user=request.user)
            .order_by('-created_at')
            .select_related('article__category', 'article')
            .prefetch_related('article__sub_interests')
        )
        bookmarks = []
        for b in qs:
            art = b.article
            bookmarks.append({
                'id': art.id,
                'title': art.title,
                'image_url': art.image_url,
                'source': art.source,
                'url': art.url,
                'category': getattr(art.category, 'name', ''),
                'sub_categories': list(art.sub_interests.values_list('name', flat=True)),
                'published_at': art.published_at.isoformat() if getattr(art, 'published_at', None) else None,
            })

    return render(request, 'mypage_scraparticle.html', {'article_bookmarks': bookmarks})
    
    
 # 레벨 테스트 관련 부분   
from .services import (
    load_bank, pick_self_ids, next_question, grade_and_advance, score_to_level
)

from terms.models import TermBookmark

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


#레벨 테스트 보고 나면 결과에 맞는 레벨 & XP 부여되도록 설정
LEVEL_TOTAL_XP = {1: 0, 2: 1715, 3: 5635, 4: 12985, 5: 25725}

def result_page(request):
    state = request.session.get(SESSION_KEY)
    if not state:
        return redirect("level_test:page")

    total = float(state["total_self"]) + float(state["total_knowledge"])
    level = score_to_level(total)

    debug_info = None

    if request.user.is_authenticated:
        user = request.user
        user.level_score = int(total)

        target = LEVEL_TOTAL_XP.get(level, 0)

        # 이번에 실제로 더해준 XP(지급 XP)
        reward_xp = max(0, target - user.total_score)

        user.total_score += reward_xp
        user.save(update_fields=["level_score", "total_score", "level"])

        print(
            f"[LEVEL TEST] user={user.email} | "
            f"reward_xp=+{reward_xp} | "
            f"total_score={user.total_score} | "
            f"level={user.level}",
            flush=True
        )

        debug_info = {
            "reward_xp": reward_xp,
            "total_score": user.total_score,
            "level": user.level,
        }

    return render(request, "level_test_result.html", {
        "total": total,
        "level": level,  # 레벨테스트 판정 레벨(점수 기반)
        "user_name": request.user.username if request.user.is_authenticated else "게스트",
        "debug_info": debug_info,
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
def update_username(request):
    new_username = request.POST.get('username', '').strip()
    if not new_username:
        messages.error(request, '사용자 이름(username)을 입력해 주세요.')
        return redirect('edit')

    if len(new_username) > 20:
        messages.error(request, '사용자 이름은 20자 이내여야 합니다.')
        return redirect('edit')

    if User.objects.exclude(pk=request.user.pk).filter(username=new_username).exists():
        messages.error(request, '이미 사용 중인 사용자 이름입니다.')
        return redirect('edit')

    request.user.username = new_username
    request.user.save(update_fields=['username'])
    messages.success(request, '사용자 이름이 변경되었습니다.')
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
    bookmarks = []
    if request.user.is_authenticated:
        qs = TermBookmark.objects.filter(user=request.user).select_related('term').order_by('-created_at')
        bookmarks = [{'word': b.term.name, 'definition': b.term.explanation, 'created_at': b.created_at} for b in qs]
    return render(request, 'mypage_scrapterm.html', {'bookmarks': bookmarks})
