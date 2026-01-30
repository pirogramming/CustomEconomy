from django.shortcuts import render, HttpResponse

def quiz_view(request) :
	return render(request, 'quiz.html')