from django.shortcuts import render, HttpResponse

def articleList_view(request) :
	return render(request, 'articleList.html')
