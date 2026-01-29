from django.shortcuts import render, HttpResponse

def mypage_view(request) :
	return render(request, 'mypage.html')

def login_view(request) :
	return render(request, 'login.html')

def signup_view(request) :
	return render(request, 'signup.html')

def league_view(request) :
	return render(request, 'league.html')