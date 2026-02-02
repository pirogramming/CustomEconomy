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
from quizzes.models import Quiz, QuizChoice, QuizAnswer
from articles.models import Article, Category

def load_master_dictionary():
    """
    [용어 사전 데이터 로드]
    master_dictionary.json의 Key-Value 구조를 Term 모델에 저장합니다.
    """
    file_path = 'scripts/data/master_dictionary.json'
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    for name, exp in data.items():
        # 중복 방지를 위해 get_or_create 사용 (용어 이름 기준)
        term, created = Term.objects.get_or_create(
            name=name, 
            defaults={'explanation': exp}
        )
        if created: count += 1
        
    print(f"✅ 용어 사전: {count}개의 새로운 용어 이식 완료.")

def load_concept_bank():
    """
    [기초 퀴즈 데이터 로드]
    ERD 구조상 Quiz는 반드시 Article에 종속되어야 하므로, 
    기사 원문이 없는 기초 데이터는 'System' 출처의 가상 기사를 생성하여 연결합니다.
    """
    file_path = 'scripts/data/concept_bank.json'
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_quiz = 0
    for cat_name, quizzes in data.items():
        # 1. 카테고리 생성 및 가상 기사(Article) 생성
        # ERD의 Article 모델 필수 필드(url, source, published_at) 충족을 위한 로직
        category, _ = Category.objects.get_or_create(name=cat_name)
        
        # Article의 url은 Unique 제약조건이 있으므로 카테고리별 고유 URL 부여
        article, _ = Article.objects.get_or_create(
            url=f"https://base-learning.com/{cat_name}/intro", 
            defaults={
                'category': category,
                'title': f"{cat_name} 기초 학습 가이드",
                'content': f"{cat_name} 분야의 기초 개념을 다지는 시스템 제공 퀴즈 세트입니다.",
                'source': 'System', # 실제 언론사 기사가 아님을 구분하기 위한 표기
                'published_at': timezone.now()
            }
        )

        for q in quizzes:
            # 2. Quiz 생성 (질문 내용으로 중복 체크)
            quiz, created = Quiz.objects.get_or_create(
                article=article,
                question=q['question'],
                defaults={
                    'level': 1,
                    'type': 'multiple_choice'
                }
            )

            if created:
                # 3. QuizChoice 생성 (JSON의 options 리스트 개수만큼 반복 생성)
                for opt in q['options']:
                    QuizChoice.objects.create(
                        quiz=quiz,
                        choice_text=opt,
                        # 현재 선택지가 JSON에 명시된 정답(answer)과 일치하면 True 저장
                        is_correct=(opt == q['answer'])
                    )
                
                # 4. QuizAnswer 생성 (Quiz와 1:1 관계인 해설 데이터)
                QuizAnswer.objects.create(
                    quiz=quiz,
                    explanation=q['explanation']
                )
                total_quiz += 1

    print(f"✅ 기초 퀴즈: {total_quiz}세트(가상 기사 포함) 이식 완료.")

if __name__ == "__main__":
    print("🚀 데이터베이스 이식을 시작합니다...")
    try:
        load_master_dictionary()
        load_concept_bank()
        print("\n✨ 모든 데이터가 ERD 구조에 맞춰 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")