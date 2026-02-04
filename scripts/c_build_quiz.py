import google.generativeai as genai
import json
import os
import time
import re
from dotenv import load_dotenv

# 1. 설정 (환경변수나 직접 입력)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')

# 설정값
# ✅ 카테고리별 목표 수량을 다르게 설정하기 위한 구조
CATEGORIES_CONFIG = {
    "대분류": {
        "names": ["경제", "금융", "기업", "증권", "부동산"],
        "target": 7  # 기사에 소분류가 없을 때를 대비한 보조용
    },
    "소분류": {
        "names": ["물가/인플레", "고용/지표", "환율/외환", "세금/재정", "통화/금리", "은행/대출",
                  "보험/카드", "가상자산", "국내증시", "해외증시", "채권/상품", "반도체",
                  "자동차/모빌리티", "IT/플랫폼", "실적/경영", "부동산정책", "매매/분양", "임대차/전세"],
        "target": 10 # 기사 소분류와 매칭될 메인 학습용
    }
}
BATCH_SIZE = 15           # 한 번 호출 시 요청할 문제 수 (RPD 절약용)
SAVE_PATH = "scripts/data/c_quiz.json"

def generate_quizzes(target_name, count):
    """AI에게 퀴즈 생성을 요청하는 함수"""
    prompt = f"""
    경제 초보자를 위한 '{target_name}' 관련 기초 상식 및 원리 퀴즈 {count}개를 만들어줘.
    
    작성 가이드 (B유형 '용어 정의'와 차별화할 것):
    1. 단순 정의(예: ~란 무엇인가?)는 피하고, 실제 경제 상황이나 현상을 예시로 들어줘.
    2. '원인과 결과'(예: 금리가 오르면 대출 이자는 어떻게 될까?) 같은 인과관계를 묻는 문제를 포함해줘.
    3. 일상생활에서 접할 수 있는 구체적인 상황(Scenario)을 제시해줘.
    4. 출력 형식은 반드시 JSON 리스트로만 대답하고, 정답의 위치는 무작위로 섞어줘.
    5. 출력 시 JSON 마크다운(json ... )을 사용하지 말고, 설명이나 인사말 없이 오직 순수한 JSON 문자열만 출력해줘.

    [
      {{
        "question": "질문 내용 (상황이나 원리 중심)",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": "정답 내용",
        "explanation": "이 현상이 왜 일어나는지 초보자 눈높이에서 설명"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # --- [보강된 정제 로직] ---
        # 1. ```json 또는 ``` 같은 마크다운 태그가 있다면 제거
        clean_text = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
        
        # 2. 정규표현식으로 [ ] 리스트 부분만 확실하게 추출
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            # 리스트 형식이 아니면 전체 텍스트 시도
            return json.loads(clean_text)
            
    except Exception as e:
        print(f"      ❌ API 호출 또는 JSON 파싱 중 오류 발생: {e}")
        # 에러 발생 시 response.text를 출력해서 원인을 파악하기 좋게 함 (선택)
        # print(f"DEBUG: AI 응답 내용 -> {response.text}") 
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
        target_count = config["target"] # 대분류 7, 소분류 10 적용
        
        for name in config["names"]:
            current_quizzes = final_bank.get(name, [])
            
            # ✅ 이미 목표 수량을 채웠다면 건너뛰기
            if len(current_quizzes) >= target_count:
                print(f"⏩ '{name}'({group_type})는 이미 {len(current_quizzes)}개가 있어 건너뜁니다.")
                continue

            print(f"\n🚀 '{name}'({group_type}) 생성 시작 ({len(current_quizzes)}/{target_count})")
            seen_questions = {q['question'].strip() for q in current_quizzes}
            
            while len(current_quizzes) < target_count:
                needed = target_count - len(current_quizzes)
                fetch_count = min(needed, BATCH_SIZE)
                
                print(f"   - {len(current_quizzes)}/{target_count} 진행 중... (새로운 {fetch_count}개 요청)")
                new_items = generate_quizzes(name, fetch_count)
                
                if not new_items:
                    print("     ⚠️ 데이터를 가져오지 못했습니다.")
                    break
                
                added_count = 0
                for q in new_items:
                    q_text = q['question'].strip()
                    if q_text not in seen_questions:
                        seen_questions.add(q_text)
                        current_quizzes.append(q)
                        added_count += 1
                
                print(f"     ✅ +{added_count}개 추가 완료.")

                # 세션 저장
                final_bank[name] = current_quizzes
                with open(SAVE_PATH, "w", encoding="utf-8") as f:
                    json.dump(final_bank, f, ensure_ascii=False, indent=4)
                
                time.sleep(3) # RPD 제한 방지

    print(f"\n✨ 모든 작업이 완료되었습니다!")
    print(f"📂 저장 위치: {SAVE_PATH}")

if __name__ == "__main__":
    run_main()