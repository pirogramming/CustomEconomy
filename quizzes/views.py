from django.shortcuts import render, HttpResponse

def quiz_view(request) :
	level = request.GET.get('level', 'AI_LV1')
	context = {
		'level': level
	}
	return render(request, 'quiz.html', context)