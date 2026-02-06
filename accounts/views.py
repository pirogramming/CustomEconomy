from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
# 👇 [핵심 수정 1] User 모델을 가져오기 위해 꼭 필요합니다!
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm 
from django.contrib.auth.decorators import login_required
from quizzes.models import QuizResult


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

@login_required
def scrap_article_view(request):
    return render(request, 'mypage_scraparticle.html')

@login_required
def edit_view(request):
    return render(request, 'mypage_edit.html')
    