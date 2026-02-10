import google.generativeai as genai
import json
import os
import time
import re
from dotenv import load_dotenv

# 1. 설정 (환경변수나 직접 입력)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# 카테고리별 목표 수량을 다르게 설정하기 위한 구조
CATEGORIES_CONFIG = {
    "대분류": { # 기사에 소분류가 없을 때를 대비한 보조용
        "names": ["경제", "금융", "기업", "증권", "부동산"],
        "target_per_level": 10  # 레벨당 10개 (총 250개)
    },
    "소분류": {
        "names": ["물가/인플레", "고용/지표", "환율/외환", "세금/재정", "통화/금리", "은행/대출",
                  "보험/카드", "가상자산", "국내증시", "해외증시", "채권/상품", "반도체",
                  "자동차/모빌리티", "IT/플랫폼", "실적/경영", "부동산정책", "매매/분양", "임대차/전세"],
        "target_per_level": 10  # 레벨당 10개 (총 900개)
    }
}
BATCH_SIZE = 15  # 한 번 호출 시 요청할 문제 수 (RPD 절약용)
SAVE_PATH = "scripts/data/c_level_quiz.json"

def generate_quizzes(target_name, level, count):
    """AI에게 특정 레벨의 퀴즈 생성을 요청하는 함수"""

    # 레벨별 상세 가이드 정의
    level_guides = {
        1: "Level 1 (입문): 생활 밀착 사례, 1단계 인과 (A → B), 직관적으로 풀 수 있는 난이도",
        2: "Level 2 (기초 뉴스 이해): 정책/지표에 따른 시장 반응, 2단계 인과 (A → B → C)",
        3: "Level 3 (중급 구조 이해): 금리/환율/증시 연결 등 복합 인과, 함정 오답 포함",
        4: "Level 4 (고급 정책 해석): 복합 정책 조합, 시차/역설적 결과 등 심화 분석",
        5: "Level 5 (전문가 추론): 다변수 거시 시나리오, 복합 경제 판단 등 최고 난이도"
    }

    prompt = f"""
    경제 분야 '{target_name}' 관련 {level_guides[level]} 퀴즈 {count}개를 만들어줘.
    
    작성 가이드:
    1. 반드시 "quiz_type": "C" 필드를 포함할 것.
    2. 반드시 "level": {level} 필드를 포함할 것.
    3. 단순 용어 정의(B유형)는 피하고, 실제 상황(Scenario)이나 인과관계를 묻는 문제를 만들 것.
    5. 앞서 낸 문제와 동일한 문제 금지하고 정답 위치는 무작위로 섞을 것.
    4. 출력 형식은 반드시 JSON 리스트로만 대답할 것.
    5. 출력 시 JSON 마크다운(json ... )을 사용하지 말고, 설명이나 인사말 없이 오직 순수한 JSON 문자열만 출력할 것.

    [
      {{
        "quiz_type": "C",
        "level": {level},
        "question": "질문 내용 (상황이나 원리 중심)",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": "정답 내용",
        "explanation": "해당 레벨 눈높이에 맞는 상세 설명"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        clean_text = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        return json.loads(match.group(0)) if match else json.loads(clean_text)
    except Exception as e:
        print(f"      ❌ API 호출 또는 JSON 파싱 오류: {e}")
        return []
    
def run_main():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    final_bank = {}
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            try:
                final_bank = json.load(f)
                print(f"📂 기존 데이터를 불러왔습니다. 현재 저장된 카테고리 수: {len(final_bank)}")
            except:
                final_bank = {}

    for group_type, config in CATEGORIES_CONFIG.items():
        target_num = config["target_per_level"]
        
        for name in config["names"]:
            current_quizzes = final_bank.get(name, [])
            print(f"\n🚀 '{name}'({group_type}) 작업 시작")

            # 레벨 1부터 5까지 순회
            for lv in range(1, 6):
                # 현재 레벨의 문제만 필터링
                lv_existing = [q for q in current_quizzes if q.get('level') == lv]
                
                if len(lv_existing) >= target_num:
                    print(f"  ⏩ Lv.{lv}: 이미 {len(lv_existing)}개가 있어 건너뜜.")
                    continue

                needed = target_num - len(lv_existing)
                print(f"  - Lv.{lv}: {len(lv_existing)}/{target_num} 진행 중 ({needed}개 요청)")
                
                # lv 인자를 추가해서 호출
                new_items = generate_quizzes(name, lv, needed)
                
                added_count = 0
                seen_questions = {q['question'].strip() for q in current_quizzes}
                
                for q in new_items:
                    q_text = q['question'].strip()
                    if q_text not in seen_questions:
                        # 데이터 정합성을 위해 명시적으로 삽입
                        q['level'] = lv
                        q['quiz_type'] = 'C'
                        
                        seen_questions.add(q_text)
                        current_quizzes.append(q)
                        added_count += 1
                
                print(f"    ✅ Lv.{lv}: +{added_count}개 추가 완료.")

                # 레벨 하나 끝날 때마다 중간 저장
                final_bank[name] = current_quizzes
                with open(SAVE_PATH, "w", encoding="utf-8") as f:
                    json.dump(final_bank, f, ensure_ascii=False, indent=4)
                
                time.sleep(3) # API 속도 제한 방지

    print(f"\n✨ 작업 완료! 저장 위치: {SAVE_PATH}")

if __name__ == "__main__":
    run_main()