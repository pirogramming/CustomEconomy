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

def load_concept_bank():
    """[C유형 기초 데이터] 카테고리별 기초 퀴즈 로드"""
    file_path = 'scripts/data/concept_bank.json'
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_quiz = 0
    for cat_name, quizzes in data.items():
        # 1. 카테고리 가져오기
        category, _ = Category.objects.get_or_create(name=cat_name)

        for q in quizzes:
            # 2. Quiz 생성 (설명/해설 필드가 Quiz 모델로 통합됨)
            quiz, created = Quiz.objects.get_or_create(
                category=category,
                question=q['question'],
                defaults={
                    'article': None,       # C유형은 기사 연결 없이 카테고리만 연결
                    'level': 1,
                    'type': 'C',
                    'explanation': q['explanation'] # 모델 통합으로 여기서 바로 저장!
                }
            )

            if created:
                # 3. QuizChoice 생성
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
        load_concept_bank()
        print("\n✨ 모든 데이터가 통합된 Quiz 모델 구조에 맞춰 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")