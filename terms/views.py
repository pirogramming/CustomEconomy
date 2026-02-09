from django.shortcuts import render
from django.conf import settings
import json
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json as _json
from .models import TermBookmark


def terms_view(request):
	q = request.GET.get('q', '').strip()

	json_path = Path(settings.BASE_DIR) / 'scripts' / 'data' / 'master_dictionary.json'
	items = []
	try:
		with open(json_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
			items = list(data.items())
	except Exception:
		items = []

	# 검색어로 필터링 (단어 또는 뜻에 포함되는지)
	if q:
		q_lower = q.lower()
		items = [ (w, d) for w, d in items if q_lower in w.lower() or q_lower in d.lower() ]

	# 가나다(한글) 먼저, 그 다음 영어/기타 순으로 정렬
	korean_items = []
	other_items = []
	for w, d in items:
		first = w[0] if w else ''
		if first and ('\uAC00' <= first <= '\uD7A3' or '\u3131' <= first <= '\u318E'):
			korean_items.append((w, d))
		else:
			other_items.append((w, d))

	korean_items.sort(key=lambda x: x[0])
	other_items.sort(key=lambda x: x[0].lower())

	dictionary_items = korean_items + other_items

	bookmarked_words = set()
	if request.user.is_authenticated:
		bookmarked_words = set(TermBookmark.objects.filter(user=request.user).values_list('word', flat=True))

	return render(request, 'terms.html', {
		'dictionary_items': dictionary_items,
		'q': q,
		'count': len(dictionary_items),
		'bookmarked_words': bookmarked_words,
	})


@login_required
@require_POST
def bookmark_term(request):
	# Accept JSON body
	try:
		payload = _json.loads(request.body.decode('utf-8')) if request.body else {}
	except Exception:
		payload = {}

	word = payload.get('word') or request.POST.get('word')
	definition = payload.get('definition') or request.POST.get('definition')

	if not word:
		return JsonResponse({'ok': False, 'error': 'no_word'}, status=400)

	# store in DB
	obj, created = TermBookmark.objects.get_or_create(
		user=request.user,
		word=word,
		defaults={'definition': definition or ''}
	)
	if not created and definition and obj.definition != definition:
		obj.definition = definition
		obj.save(update_fields=['definition'])

	# return updated bookmark list
	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = [{'word': b.word, 'definition': b.definition, 'created_at': b.created_at.isoformat()} for b in qs]
	return JsonResponse({'ok': True, 'created': created, 'bookmarks': data})


@login_required
def bookmarks_json(request):
	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = [{'word': b.word, 'definition': b.definition, 'created_at': b.created_at.isoformat()} for b in qs]
	return JsonResponse({'ok': True, 'bookmarks': data})


@login_required
@require_POST
def unbookmark_term(request):
	try:
		payload = _json.loads(request.body.decode('utf-8')) if request.body else {}
	except Exception:
		payload = {}

	word = payload.get('word') or request.POST.get('word')
	if not word:
		return JsonResponse({'ok': False, 'error': 'no_word'}, status=400)

	deleted_count, _ = TermBookmark.objects.filter(user=request.user, word=word).delete()
	deleted = deleted_count > 0

	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = [{'word': b.word, 'definition': b.definition, 'created_at': b.created_at.isoformat()} for b in qs]
	return JsonResponse({'ok': True, 'deleted': deleted, 'bookmarks': data})
