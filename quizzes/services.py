import google.generativeai as genai
import json
import os
import random
import re
from django.conf import settings
from django.db import models, transaction
from articles.models import Article
from accounts.models import Interest, UserInterest
from terms.models import Term 
from .models import Quiz, QuizChoice
from dotenv import load_dotenv
from explanations.models import ArticleExplanation

# .env 파일 로드
load_dotenv()

# Gemini 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def link_terms_to_article(article_obj):
    """
    기사 본문에서 등록된 용어(Term)가 있는지 찾아 ManyToMany 관계로 연결
    """
    # 모든 용어를 가져와서 본문에 포함되어 있는지 확인 (데이터가 많으면 최적화 필요)
    all_terms = Term.objects.all()
    content = article_obj.content
    
    linked_count = 0
    for term in all_terms:
        # 본문에 용어 이름이 포함되어 있다면 연결
        if term.name in content:
            article_obj.terms.add(term)
            linked_count += 1
    
    return linked_count

def create_ai_quiz_from_article(article_obj):
    """
    Gemini API를 사용하여 기사 기반 A유형 퀴즈 생성 및 캐싱
    """
    if Quiz.objects.filter(article=article_obj, type='A').exists():
        return 0

    prompt = f"""
    당신은 경제 교육 전문가입니다. 다음 기사를 바탕으로 입문자를 위한 객관식 퀴즈 3개를 JSON 형식으로 만드세요.
    기사 제목: {article_obj.title}
    기사 내용: {article_obj.content}
    [출제 구성 가이드]:
    1. 문제 1~2 (사실 확인): 기사에 명시된 핵심 수치, 사건, 기관의 움직임을 파악했는지 묻는 문제.
    2. 문제 3 (기초 원리): 기사 속 사건이 경제적으로 왜 일어났는지, 어떤 영향을 주는지 기초 원리를 연결하는 문제.

    [필수 규칙]:
    - 유형 B가 '용어 이름'을 묻기 때문에, 정답이 단순히 경제 용어 명칭인 문제는 제외하세요.
    - 정답은 반드시 기사 내용에 근거가 있어야 하며, '교훈' 같은 추상적 질문은 금지합니다.
    - 해설(explanation)은 유저가 기사를 복기하며 경제 상식을 얻을 수 있도록 친절하게 작성하세요.
    - 출력은 반드시 순수 JSON 리스트 형식으로만 하세요.
    [JSON 형식]:
    [
      {{
        "question": "질문",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": "정답",
        "explanation": "해설"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        # JSON 부분만 추출
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if not json_match: return 0
        
        quiz_data = json.loads(json_match.group(0))
        created_count = 0
        
        # DB 트랜잭션 시작 (데이터 저장 안정성 보장)
        with transaction.atomic():
            # 동시성 방어
            if Quiz.objects.filter(article=article_obj, type='A').exists():
                return 0

            for item in quiz_data:
                quiz, created = Quiz.objects.get_or_create(
                    article=article_obj,
                    question=item['question'],
                    defaults={
                        'category': article_obj.category,
                        'explanation': item['explanation'],
                        'type': 'A',
                        'level': 1
                    }
                )
                if created:
                    created_count += 1
                    for option in item['options']:
                        QuizChoice.objects.create(
                            quiz=quiz,
                            choice_text=option,
                            is_correct=(option == item['answer'])
                        )
        return created_count
    except Exception as e:
        print(f"❌ AI 생성 실패: {e}")
        return 0

def create_type_b_quiz(article_obj):
    # 기사 본문에 연결된 용어들 가져오기
    terms_qs = article_obj.terms.all()
    
    if terms_qs.exists():
        # [기사 속 단어가 있는 경우] 기사에 포함된 모든 단어
        selected_terms = terms_qs.order_by('?')
        is_from_article = True
    else:
        # [기사 속 단어가 없는 경우] 전체 DB에서 랜덤하게 3개를 뽑기
        selected_terms = Term.objects.all().order_by('?')[:3]
        is_from_article = False
    
    if not selected_terms:
        return 0

    created_count = 0
    for term_obj in selected_terms:
        prefix = "📌 [기사 속 용어]" if is_from_article else "💡 [경제 기초 단어]"
        question_text = f"{prefix} 다음 설명이 가리키는 경제 용어는?\n\n- \"{term_obj.explanation}\""
        
        # 중복 체크: 이 기사에 대해 동일한 용어 퀴즈가 이미 있는지 확인
        if not Quiz.objects.filter(article=article_obj, type='B', question=question_text).exists():
            quiz = Quiz.objects.create(
                article=article_obj,
                type='B',
                category=article_obj.category, 
                interest=None,
                question=question_text,
                explanation=f"정답은 '{term_obj.name}'입니다.",
                level=1
            )
            
            # 오답 선택지 생성 (나머지 용어 중 랜덤 3개)
            other_names = list(Term.objects.exclude(id=term_obj.id).order_by('?')[:3].values_list('name', flat=True))
            choices = [term_obj.name] + other_names
            random.shuffle(choices)

            for choice_text in choices:
                QuizChoice.objects.create(
                    quiz=quiz,
                    choice_text=choice_text,
                    is_correct=(choice_text == term_obj.name)
                )
            created_count += 1
            
    return created_count

def get_quiz_session_set(article_obj, target_level=1):
    """
    최종적으로 3문제를 반환 (A: 기사 분석, B: 용어 학습, C: 경제 상식)
    """
    # 1. 퀴즈 생성 시도 (A유형 AI 생성 및 B유형 용어 연결)
    link_terms_to_article(article_obj)
    create_ai_quiz_from_article(article_obj)
    create_type_b_quiz(article_obj)

    final_quiz_set = []

    # [A] 현재 기사 전용 (AI 생성)
    quiz_a = Quiz.objects.filter(article=article_obj, type='A').order_by('?').first()
    if quiz_a:
        final_quiz_set.append(quiz_a)

    # [B] 용어 퀴즈 (기사 관련 우선 -> 없으면 일반 용어)
    quiz_b = Quiz.objects.filter(article=article_obj, type='B').order_by('?').first()
    if not quiz_b:
        # 기사와 직접 연결된 용어 퀴즈가 없다면 전체 B유형 중 하나 선택
        quiz_b = Quiz.objects.filter(type='B').order_by('?').first()
    
    if quiz_b:
        final_quiz_set.append(quiz_b)
    
    # [C] 카테고리 맞춤 상식
    quiz_c = None
    
    # 1순위: 기사에 연결된 소분류(Interest) 중 하나를 랜덤하게 골라 C유형 퀴즈 찾기
    sub_interest = article_obj.sub_interests.all().order_by('?').first()
    if sub_interest:
        quiz_c = Quiz.objects.filter(
            type='C', 
            interest=sub_interest, 
            level=target_level  # 기사 레벨과 일치하는 퀴즈만
        ).order_by('?').first()

    # 2순위: 소분류 퀴즈가 없다면, 기사의 대분류(Category) 기반 C유형 퀴즈 찾기
    if not quiz_c:
        quiz_c = Quiz.objects.filter(
            type='C', 
            category=article_obj.category,
            level=target_level  # 기사 레벨과 일치하는 퀴즈만
        ).order_by('?').first()

    if quiz_c:
        final_quiz_set.append(quiz_c)
    
    # 2. 만약 어떤 이유로든 3개가 안 된다면
    if len(final_quiz_set) < 3:
        already_ids = [q.id for q in final_quiz_set]
        
        # 타 기사의 A유형은 절대 안 되므로, B(용어)나 해당 카테고리의 C(상식) 중에서만 추가 보충
        extra_quizzes = Quiz.objects.filter(
            models.Q(type='B') | models.Q(type='C', category=article_obj.category, level=target_level)
        ).exclude(id__in=already_ids).order_by('?')[:(3 - len(final_quiz_set))]
        
        final_quiz_set.extend(extra_quizzes)

    # 3. 반환 (최대 3개)
    return final_quiz_set[:3]