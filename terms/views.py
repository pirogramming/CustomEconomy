from django.shortcuts import render, HttpResponse

def terms_view(request) :
	return render(request, 'terms.html')