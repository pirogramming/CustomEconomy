from django.shortcuts import render
from django.conf import settings
import json
from pathlib import Path
import random
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json as _json
from .models import TermBookmark, Term
import codecs
import re


def _decode_unicode_escapes(text: str) -> str:
    """Convert literal \\uXXXX escape sequences to real characters.

    Occasionally terms have been stored in the database with literal
    escape sequences like \\u0026 instead of the real character &.
    This function replaces those patterns while preserving all other text.
    """
    if not text or "\\u" not in text:
        return text
    # Match pattern: \\ followed by u and 4 hex digits
    def replace_escape(m):
        hex_str = m.group(1)
        try:
            return chr(int(hex_str, 16))
        except Exception:
            return m.group(0)
    return re.sub(r'\\u([0-9a-fA-F]{4})', replace_escape, text)



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

	# 검색어로 필터링 (단어 매칭 -> 뜻 매칭 순서)
	word_matches = []
	def_matches = []
	if q:
		q_lower = q.lower()
		word_matches = [ (w, d) for w, d in items if q_lower in w.lower() ]
		def_matches = [ (w, d) for w, d in items if q_lower in d.lower() and q_lower not in w.lower() ]
		items = word_matches + def_matches

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
		bookmarked_words = set(TermBookmark.objects.filter(user=request.user).values_list('term__name', flat=True))

	# 검색 중이면 그룹 유지, 아니면 랜덤 순서로 노출
	count = len(dictionary_items)
	if q:
		count = len(word_matches) + len(def_matches)
	else:
		random.shuffle(dictionary_items)

	return render(request, 'terms.html', {
		'dictionary_items': dictionary_items,
		'word_matches': word_matches,
		'def_matches': def_matches,
		'q': q,
		'count': count,
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
	# ensure any escaped unicode sequences are converted before storing
	if word and "\\u" in word:
		word = _decode_unicode_escapes(word)
	if definition and "\\u" in definition:
		definition = _decode_unicode_escapes(definition)

	if not word:
		return JsonResponse({'ok': False, 'error': 'no_word'}, status=400)

	# store in DB
	# find or create Term
	term_obj, _ = Term.objects.get_or_create(name=word, defaults={'explanation': definition or ''})

	obj, created = TermBookmark.objects.get_or_create(
		user=request.user,
		term=term_obj
	)

	# return updated bookmark list (serialize as word/definition for compatibility)
	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = []
	for b in qs:
		word = _decode_unicode_escapes(b.term.name)
		definition = _decode_unicode_escapes(b.term.explanation)
		data.append({'word': word, 'definition': definition, 'created_at': b.created_at.isoformat()})
	return JsonResponse({'ok': True, 'created': created, 'bookmarks': data})


@login_required
def bookmarks_json(request):
	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = []
	for b in qs:
		word = _decode_unicode_escapes(b.term.name)
		definition = _decode_unicode_escapes(b.term.explanation)
		data.append({'word': word, 'definition': definition, 'created_at': b.created_at.isoformat()})
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

	# delete by related term name
	deleted_count, _ = TermBookmark.objects.filter(user=request.user, term__name=word).delete()
	deleted = deleted_count > 0

	qs = TermBookmark.objects.filter(user=request.user).order_by('-created_at')
	data = []
	for b in qs:
		word = _decode_unicode_escapes(b.term.name)
		definition = _decode_unicode_escapes(b.term.explanation)
		data.append({'word': word, 'definition': definition, 'created_at': b.created_at.isoformat()})
	return JsonResponse({'ok': True, 'deleted': deleted, 'bookmarks': data})
