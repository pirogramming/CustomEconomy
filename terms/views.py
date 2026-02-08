from django.shortcuts import render
from django.conf import settings
import json
from pathlib import Path


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

	return render(request, 'terms.html', {
		'dictionary_items': dictionary_items,
		'q': q,
		'count': len(dictionary_items),
	})
