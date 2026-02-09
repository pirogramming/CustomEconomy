import os
import sys
import django

# 1. Django 환경 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from articles.models import Category
from accounts.models import Interest

def run():
    # --- 1. 대분류 (Category - UI 필터링용) ---
    categories = ["경제", "금융", "기업", "증권", "부동산"]
    print("🚀 1. 대분류(Category) 생성 중...")
    for name in categories:
        cat, created = Category.objects.get_or_create(name=name)
        if created: print(f"   ✅ 생성: {name}")

    # --- 2. 관심 분야 (Interest TYPE='MAIN' - 유저 페르소나용) ---
    main_interests = [
        "투자", 
        "부동산", 
        "대출/금융",      
        "소비", 
        "환율/해외",      
        "세금/정책",      
        "자영업/사업자",  
        "취업/고용"       
    ]
    print("\n🚀 2. 관심 분야(Interest MAIN) 생성 중...")
    for name in main_interests:
        obj, created = Interest.objects.get_or_create(
            name=name, 
            defaults={'category_type': 'MAIN'} 
        )
        if created: print(f"   ✅ 생성: {name}")

    # --- 3. 소분류 (Interest TYPE='SUB' - 추천 엔진/약점 분석용) ---
    sub_interests = [
        "물가/인플레", "고용/지표", "환율/외환", "세금/재정", "통화/금리", "은행/대출",
        "보험/카드", "가상자산", "국내증시", "해외증시", "채권/상품", "반도체",
        "자동차/모빌리티", "IT/플랫폼", "실적/경영", "부동산정책", "매매/분양", "임대차/전세"
    ]
    print("\n🚀 3. 소분류(Interest SUB) 생성 중...")
    for name in sub_interests:
        obj, created = Interest.objects.get_or_create(
            name=name, 
            defaults={'category_type': 'SUB'}
        )
        if created: print(f"   ✅ 생성: {name}")

    print("\n✨ 모든 기초 데이터(Category 5, MAIN 8, SUB 18) 설정이 완료되었습니다!")

if __name__ == "__main__":
    run()