import re
import random
from typing import List, Optional, Tuple, Literal
from .models import Quiz, QuizChoice
from articles.models import Article, Category
from terms.models import Term, ArticleTerm

# -----------------------------
# 1) 설정 및 키워드 (카테고리 가중치 추가)
# -----------------------------
ECON_KEYWORDS = [
    "금리","인상","인하","물가","인플레이션","GDP","성장률","수출","수입","무역",
    "주식","주가","코스피","코스닥","상장","채권","배당","공매도","매수","매도",
    "기업","영업이익","매출","적자","흑자","반도체","플랫폼","부동산","아파트",
    "청약","분양","환율","달러","원화","% ","조원","억원","bp"
]

CATEGORY_WEIGHTS = {
    "증권": ["코스피", "코스닥", "나스닥", "증시", "주가", "상장", "공매도", "시가총액", "외국인", "기관", "매수", "매도"],
    "부동산": ["아파트", "매매가", "집값", "전세", "월세", "청약", "분양", "재건축", "공급", "임대", "LTV"],
    "경제": ["금리", "물가", "인플레이션", "한은", "GDP", "성장률", "수출", "수입", "무역수지", "환율", "기준금리"],
    "기업": ["실적", "영업이익", "매출", "영업익", "M&A", "인수", "합병", "신사업", "공시"],
    "국제": ["미국", "중국", "유럽", "협상", "타결", "공급망", "FTA"]
}

STRONG_KEYWORDS = ["코스피", "코스닥", "지수", "연준", "금리", "환율", "비트코인"]
ACTION_WORDS = ["발동", "기록", "붕괴", "하락", "상승", "급락", "급등", "타결", "확대"]
BAD_WORDS = ["최고", "뷰", "자랑", "인기", "프리미엄", "아름다운"]

# -----------------------------
# 2) 헬퍼 함수 (로직)
# -----------------------------
def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[\.\?\!])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]

def score_sentence(sentence: str, category_name: str) -> float:
    s = sentence
    score = 0.0
    # 경제 키워드 점수
    econ_hits = sum(1 for k in ECON_KEYWORDS if k in s)
    score += min(econ_hits, 6) * 1.0
    # 카테고리 가중치
    spec_keywords = CATEGORY_WEIGHTS.get(category_name, [])
    score += sum(1 for k in spec_keywords if k in s) * 2.0
    # 강한 키워드 및 동사
    if any(k in s for k in STRONG_KEYWORDS): score += 2.5
    if any(a in s for a in ACTION_WORDS): score += 1.5
    # 수치 패턴 (의미 있는 단위 우선)
    if re.search(r"\d+(\.\d+)?\s*%|\d+\s*조|\d+\s*억|\d+\s*달러|\d+bp", s):
        score += 3.0
    # 감점
    if len(s) < 25: score -= 2.0
    if any(b in s for b in BAD_WORDS): score -= 5.0
    return score

def find_numbers(sentence: str) -> List[str]:
    patterns = [r"-?\d+(\.\d+)?\s*%", r"\d+만\d+달러", r"\d+\s*조\d+\s*억", r"\d+\s*조", r"\d+\s*억", r"\d+(\.\d+)?"]
    nums = []
    for p in patterns:
        for m in re.finditer(p, sentence):
            val = m.group(0).strip()
            if not re.fullmatch(r"\d+일", val): nums.append(val)
    return list(dict.fromkeys(nums))

def mutate_number(num: str) -> List[str]:
    s = num.replace(" ", "")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m: return []
    val = float(m.group(0))
    cands = set()
    if "%" in s:
        for d in [0.5, 1.1, 1.5]:
            cands.add(f"{val + d:.1f}%"); cands.add(f"{val - d:.1f}%")
    else:
        for p in [0.02, 0.05]:
            cands.add(f"{val*(1+p):.1f}"); cands.add(f"{val*(1-p):.1f}")
    cands.discard(num)
    return list(cands)[:3]

# -----------------------------
# 2-1) 문장 변형 및 선택지 생성 유틸
# -----------------------------

def make_cloze(sentence: str, target: str) -> str:
    """문장 내 특정 단어를 ____ 로 바꿈"""
    s = re.sub(r"\s+", " ", sentence).strip()
    if target in s:
        return s.replace(target, "____", 1)
    # 수치 형태가 약간 다를 경우 숫자만이라도 가리기
    m = re.search(r"-?\d+(\.\d+)?", target)
    if m:
        num = m.group(0)
        return re.sub(re.escape(num), "____", s, count=1)
    return s

def mutate_number_for_ox(num: str) -> str:
    """OX용 가짜 숫자 만들기 (정답은 X가 됨)"""
    s = num.replace(" ", "")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m: return num
    val = float(m.group(0))
    if "%" in s:
        delta = random.choice([0.5, 1.2, 2.0])
        new_val = val + random.choice([-delta, delta])
        return f"{new_val:.1f}%"
    pct = random.choice([0.05, 0.1])
    new_val = val * (1 + random.choice([-pct, pct]))
    return f"{new_val:.1f}".rstrip("0").rstrip(".")

def flip_action_word(sentence: str) -> Optional[Tuple[str, str]]:
    """행동 단어를 반대로 바꿈 (OX용)"""
    pairs = [
        ("상승", "하락"), ("하락", "상승"),
        ("급등", "급락"), ("급락", "급등"),
        ("순매도", "순매수"), ("순매수", "순매도"),
        ("흑자", "적자"), ("적자", "흑자"),
        ("타결", "결렬"), ("확대", "축소")
    ]
    for a, b in pairs:
        if a in sentence:
            return (a, b)
    return None

# 주체 빈칸용 데이터 (pipeline.py에 있던 것)
SUBJECT_HINTS = ["외국인", "기관", "개인투자자", "코스피", "코스닥", "연준", "한국은행", "삼성전자", "비트코인", "달러"]
SUBJECT_DISTRACTORS = {
    "코스피": ["코스닥", "환율", "나스닥"],
    "외국인": ["개인투자자", "기관", "정부"],
    "비트코인": ["금", "은", "달러"],
    "연준": ["한국은행", "유럽중앙은행", "기재부"]
}

def guess_subject(sentence: str) -> Optional[str]:
    for h in SUBJECT_HINTS:
        if h in sentence: return h
    return None

def subject_choices(subject: str) -> List[str]:
    distractors = SUBJECT_DISTRACTORS.get(subject, []).copy()
    pool = [h for h in SUBJECT_HINTS if h != subject]
    random.shuffle(pool)
    while len(distractors) < 3 and pool:
        d = pool.pop()
        if d not in distractors: distractors.append(d)
    return [subject] + distractors[:3]

# -----------------------------
# 3) 핵심 서비스 함수 (Django 모델 연동)
# -----------------------------
def link_terms_to_article(article_obj: Article):
    """[추가] 기사 본문에서 DB의 용어를 찾아 연결 (B유형 재료)"""
    all_terms = Term.objects.all()
    for term in all_terms:
        if term.name in article_obj.content:
            ArticleTerm.objects.get_or_create(article=article_obj, term=term)

# A유형 생성
def create_quiz_from_article(article_obj: Article):
    if Quiz.objects.filter(article=article_obj).exists():
        return 0
    
    category_name = article_obj.category.name if article_obj.category else "경제"
    sentences = split_sentences(article_obj.content)
    
    scored_sentences = []
    for s in sentences:
        if any(k in s for k in ECON_KEYWORDS):
            scored_sentences.append((score_sentence(s, category_name), s))
    
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s for _, s in scored_sentences[:15]]
    
    created_count = 0
    used_sentences = set() # 중복 문장 방지

    for sent in top_sentences:
        if created_count >= 5: break
        if sent in used_sentences: continue

        q_text, choices, ans_idx = None, [], -1
        
        # 1순위: 행동 반전 OX 퀴즈 (확률적으로 섞음)
        flip = flip_action_word(sent)
        if flip and random.random() < 0.3:
            orig, changed = flip
            alt_sent = sent.replace(orig, changed, 1)
            q_text = f"다음 문장은 기사 내용과 일치할까요?\n\n- {alt_sent}"
            choices = ["O", "X"]
            ans_idx = 1 # 무조건 X가 정답
            
        # 2순위: 주체 빈칸 MCQ
        elif guess_subject(sent) and random.random() < 0.4:
            subj = guess_subject(sent)
            cloze_sent = make_cloze(sent, subj)
            q_text = f"빈칸에 들어갈 대상으로 알맞은 것은?\n\n- {cloze_sent}"
            choices = subject_choices(subj)
            random.shuffle(choices)
            ans_idx = choices.index(subj)

        # 3순위: 수치 빈칸 MCQ (가장 확실한 유형)
        else:
            nums = find_numbers(sent)
            if not nums: continue
            num = nums[0]
            distractors = mutate_number(num)
            if len(distractors) < 3: continue
            
            cloze_sent = make_cloze(sent, num)
            q_text = f"빈칸에 들어갈 수치로 알맞은 것은?\n\n- {cloze_sent}"
            choices = [num] + distractors
            random.shuffle(choices)
            ans_idx = choices.index(num)

        if q_text:
            quiz = Quiz.objects.create(
                article=article_obj,
                category=article_obj.category,
                question=q_text,
                explanation=f"근거 문장: {sent}",
                type='A',
                level=2
            )
            for i, c_text in enumerate(choices):
                QuizChoice.objects.create(
                    quiz=quiz,
                    choice_text=str(c_text),
                    is_correct=(i == ans_idx)
                )
            used_sentences.add(sent)
            created_count += 1

    return created_count

# B유형 생성
def create_type_b_quiz(article_obj: Article):
    """
    기사와 연결된 Term(용어)의 '설명'을 문제로 내고, '단어 이름'을 맞히는 B유형 생성
    """
    # 1. 기사와 연관된 용어들 가져오기
    terms = article_obj.terms.all()
    if not terms.exists():
        return 0

    created_count = 0
    # 연관 용어 중 최대 2개 선정
    for term_obj in terms.order_by('?')[:2]:
        # 중복 생성 방지
        if Quiz.objects.filter(article=article_obj, question__contains=term_obj.explanation[:20]).exists():
            continue

        # 2. 오답 선택지 (다른 '단어 이름'들을 가져옴)
        other_terms = Term.objects.exclude(id=term_obj.id).order_by('?')[:3]
        if other_terms.count() < 3: continue 

        choices = [term_obj.name] + [ot.name for ot in other_terms]
        random.shuffle(choices)
        ans_idx = choices.index(term_obj.name)

        # 3. 퀴즈 저장 (질문에 '설명'을 넣음)
        quiz = Quiz.objects.create(
            article=article_obj,
            category=article_obj.category,
            question=f"다음 설명에 해당하는 경제 용어는 무엇일까요?\n\n- \"{term_obj.explanation}\"",
            explanation=f"정답: {term_obj.name}\n기사에 등장한 주요 용어입니다.",
            type='B', # 용어 기반
            level=1
        )

        for i, c_text in enumerate(choices):
            QuizChoice.objects.create(
                quiz=quiz,
                choice_text=c_text, 
                is_correct=(i == ans_idx)
            )
        created_count += 1

    return created_count

# -----------------------------
# 4) [신규] 통합 서비스 함수 (View에서 이것을 호출)
# -----------------------------

def get_quiz_session_set(article_obj: Article):
    """
    기사 상세에서 '퀴즈 풀기' 클릭 시 A, B, C 유형을 하나씩 반환
    """
    # 1. 기사와 관련된 퀴즈(A, B)가 하나도 없으면 생성 가동
    # filter(article=article_obj)를 통해 해당 기사용 퀴즈만 체크
    if not Quiz.objects.filter(article=article_obj).exists():
        link_terms_to_article(article_obj)
        create_quiz_from_article(article_obj)
        create_type_b_quiz(article_obj)

    # 2. 유형별로 랜덤하게 1개씩 추출
    quiz_a = Quiz.objects.filter(article=article_obj, type='A').order_by('?').first()
    quiz_b = Quiz.objects.filter(article=article_obj, type='B').order_by('?').first()
    
    # 3. C유형 (Bank에서 추출)
    # 기사 카테고리와 일치하는 것 우선
    quiz_c = Quiz.objects.filter(
        type='C', 
        category=article_obj.category,
        article__isnull=True
    ).order_by('?').first()
    
    # 일치하는 카테고리가 없으면 전체 상식 중 랜덤
    if not quiz_c:
        quiz_c = Quiz.objects.filter(type='C', article__isnull=True).order_by('?').first()

    # 존재하는 퀴즈만 리스트로 묶어서 반환
    return [q for q in [quiz_a, quiz_b, quiz_c] if q]