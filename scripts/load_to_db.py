import os
import sys
import json
import django
from django.utils import timezone

# 1. Django 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from terms.models import Term
from quizzes.models import Quiz, QuizChoice
from articles.models import Article, Category
from accounts.models import Interest

def load_master_dictionary():
    """[B유형 기초 데이터] 용어 사전 데이터 로드"""
    file_path = 'scripts/data/master_dictionary.json'
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    for name, exp in data.items():
        term, created = Term.objects.get_or_create(
            name=name, 
            defaults={'explanation': exp}
        )
        if created: count += 1
    print(f"✅ 용어 사전: {count}개의 용어 이식 완료.")

def load_c_quiz():
    """[C유형] 대분류와 소분류를 구분하여 DB 적재"""
    file_path = 'scripts/data/c_quiz.json'
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_quiz = 0
    for target_name, quizzes in data.items():
        # 1. 소분류(Interest)인지 대분류(Category)인지 확인
        interest = Interest.objects.filter(name=target_name).first()
        category = Category.objects.filter(name=target_name).first()

        if not interest and not category:
            print(f"⚠️ {target_name}이(가) DB에 없습니다. 확인이 필요합니다.")
            continue

        for q in quizzes:
            # 2. Quiz 생성
            quiz, created = Quiz.objects.get_or_create(
                question=q['question'],
                defaults={
                    'type': 'C',
                    'interest': interest,  # 소분류면 객체 저장, 아니면 None
                    'category': category,      # 대분류면 객체 저장, 아니면 None
                    'explanation': q['explanation'],
                    'level': 1
                }
            )

            if created:
                for opt in q['options']:
                    QuizChoice.objects.create(
                        quiz=quiz,
                        choice_text=opt,
                        is_correct=(opt == q['answer'])
                    )
                total_quiz += 1

    print(f"✅ 기초 퀴즈(C유형): {total_quiz}세트 이식 완료.")

if __name__ == "__main__":
    print("🚀 데이터베이스 이식을 시작합니다...")
    try:
        load_master_dictionary()
        load_c_quiz()
        print("\n✨ 모든 데이터가 통합된 Quiz 모델 구조에 맞춰 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")