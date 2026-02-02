from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm 


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
        # AuthenticationForm은 request를 첫 번째 인자로 받습니다.
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('articleList') # 로그인 성공 시 이동할 곳
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 3. 로그아웃 (필수 기능)
def logout_view(request):
    logout(request)
    return redirect('login')

# 4. 기타 페이지
def mypage_view(request):
    return render(request, 'mypage.html')

def league_view(request):
    return render(request, 'league.html')