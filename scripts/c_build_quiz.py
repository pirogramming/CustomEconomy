import google.generativeai as genai
import json
import os
import time
from dotenv import load_dotenv

# 1. 설정 (환경변수나 직접 입력)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')

# 설정값
CATEGORIES = ["경제", "금융", "기업", "증권", "부동산"]
TARGET_PER_CATEGORY = 30  # 카테고리당 목표 문제 수
BATCH_SIZE = 10           # 한 번 호출 시 요청할 문제 수 (RPD 절약용)
SAVE_PATH = "c_quiz/concept_bank.json"

def generate_quizzes(category, count):
    """AI에게 퀴즈 생성을 요청하는 함수"""
    prompt = f"""
    경제 학습용 기초 퀴즈 {count}개를 만들어줘.
    카테고리: {category}
    
    주의사항:
    1. 초보자도 이해할 수 있는 실생활 경제 원리를 다뤄줘.
    2. 출력 형식은 반드시 아래 JSON 구조의 '리스트'로만 대답해. 다른 설명은 하지마.
    3. 정답(answer)은 반드시 보기(options) 중 하나와 정확히 일치해야 하며, 정답의 위치는 매번 무작위로 섞어줘.
    [
      {{
        "question": "질문 내용",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": "정답 내용",
        "explanation": "왜 이게 정답인지에 대한 친절한 설명"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 마크다운 태그 제거 및 정제
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    except Exception as e:
        print(f"      ❌ API 호출 중 오류 발생: {e}")
        return []

def run_main():
    # 폴더 생성
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    # 1. 기존 데이터 불러오기 (이어쓰기 로직)
    final_bank = {}
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            try:
                final_bank = json.load(f)
                print(f"📂 기존 데이터를 불러왔습니다. 현재 저장된 카테고리: {list(final_bank.keys())}")
            except:
                final_bank = {}

    for cat in CATEGORIES:
        # 2. 이미 목표 수량을 채웠다면 건너뛰기
        current_quizzes = final_bank.get(cat, [])
        if len(current_quizzes) >= TARGET_PER_CATEGORY:
            print(f"⏩ '{cat}' 카테고리는 이미 {len(current_quizzes)}개가 있어 건너뜁니다.")
            continue

        print(f"\n🚀 '{cat}' 카테고리 생성 시작 ({len(current_quizzes)}/{TARGET_PER_CATEGORY})")
        seen_questions = {q['question'].strip() for q in current_quizzes}
        
        # 3. 목표치를 채울 때까지 반복
        while len(current_quizzes) < TARGET_PER_CATEGORY:
            needed = TARGET_PER_CATEGORY - len(current_quizzes)
            fetch_count = min(needed, BATCH_SIZE)
            
            print(f"   - {len(current_quizzes)}/{TARGET_PER_CATEGORY} 진행 중... (새로운 {fetch_count}개 요청)")
            new_items = generate_quizzes(cat, fetch_count)
            
            if not new_items:
                print("     ⚠️ 데이터를 가져오지 못했습니다. 할당량이 끝났을 수 있습니다.")
                break # 다음 카테고리로 넘어가거나 종료
            
            added_in_this_batch = 0
            for q in new_items:
                q_text = q['question'].strip()
                if q_text not in seen_questions:
                    seen_questions.add(q_text)
                    current_quizzes.append(q)
                    added_in_this_batch += 1
            
            print(f"     ✅ 이번 요청에서 {added_in_this_batch}개의 새로운 문제 추가 완료.")

            # 4. 루프 한 번 돌 때마다(매 batch마다) 즉시 파일 저장 (가장 안전)
            final_bank[cat] = current_quizzes
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(final_bank, f, ensure_ascii=False, indent=4)
            
            # API 제한(TPM)을 위해 짧게 휴식
            time.sleep(3)

    print(f"\n✨ 모든 작업이 완료되었습니다!")
    for cat, quizzes in final_bank.items():
        print(f"   📊 {cat}: {len(quizzes)}개 확보")
    print(f"📂 저장 위치: {SAVE_PATH}")

if __name__ == "__main__":
    run_main()