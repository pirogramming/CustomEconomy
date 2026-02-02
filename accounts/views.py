from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm 

# 1. 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 가입 후 자동 로그인
            return redirect('articleList')  # 메인 페이지 이름 (urls.py 확인 필요)
    else:
        form = CustomUserCreationForm()
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