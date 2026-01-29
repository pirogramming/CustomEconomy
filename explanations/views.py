from django.shortcuts import render, HttpResponse

def ai_explain_view(request) :
	return render(request, 'ai_explain.html')