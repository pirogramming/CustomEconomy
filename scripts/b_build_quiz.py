import os
import sys
import django
import random

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 모델 임포트
from terms.models import Term
from quizzes.models import Quiz, QuizChoice
from django.db import transaction

def build_quizzes():
    all_terms = list(Term.objects.all())
    total_count = len(all_terms)
    
    if total_count == 0:
        print('❌ Term 데이터가 없습니다. 먼저 용어를 등록해주세요.')
        return

    print(f'🚀 총 {total_count}개의 용어로 퀴즈 생성을 시작합니다...')

    created_count = 0
    skipped_count = 0

    with transaction.atomic():
        for term in all_terms:
            # 질문 생성
            question_text = f"다음 설명이 가리키는 경제 용어는?\n\n- \"{term.explanation}\""
            
            # 중복 생성 방지
            if Quiz.objects.filter(type='B', article__isnull=True, question=question_text).exists():
                skipped_count += 1
                continue
            
            # 퀴즈 객체 생성
            quiz = Quiz.objects.create(
                article=None,
                level=1,
                question=question_text,
                explanation=f"정답은 '{term.name}'입니다.",
                type='B'
            )
            # 랜덤하게 3개 오답 선택
            other_term_names = [t.name for t in all_terms if t.id != term.id]
            wrong_sample_count = min(len(other_term_names), 3)
            wrong_choices = random.sample(other_term_names, wrong_sample_count)

            # 정답 저장
            QuizChoice.objects.create(quiz=quiz, choice_text=term.name, is_correct=True)
            # 오답 저장
            for wc_text in wrong_choices:
                QuizChoice.objects.create(quiz=quiz, choice_text=wc_text, is_correct=False)
            
            created_count += 1

    print(f'✨ 작업 완료! 생성: {created_count}개, 건너뜀: {skipped_count}개')

if __name__ == "__main__":
    build_quizzes()