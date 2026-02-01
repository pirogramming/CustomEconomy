import os
import json
import time
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 경로 및 환경 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FILE = os.path.join(BASE_DIR, "term_800.pdf")
DICT_FILE = os.path.join(BASE_DIR, "master_dictionary.json")

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 검증된 모델 사용
model = genai.GenerativeModel("gemini-3-flash-preview")

# 설정: 19페이지부터 끝까지 40페이지씩 자동 순회
START_PAGE = 19
END_PAGE = 428
BATCH_SIZE = 40 

def get_gemini_response(text):
    prompt = f"""
    너는 경제 전문가이다. 아래 텍스트에서 경제 용어와 그 정의를 추출하라.
    - 형식: {{"용어": "초보자용 쉬운 한 문장 정의"}}
    - 반드시 순수한 JSON 객체 하나만 출력하라. 다른 텍스트는 금지한다.
    
    텍스트:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        text_res = response.text.strip()
        
        start = text_res.find("{")
        end = text_res.rfind("}") + 1
        return json.loads(text_res[start:end])
    except Exception as e:
        print(f"⚠️ 에러 발생: {e}")
        return {}

def run():
    print(f"🚀 [전체 자동 모드] 경제 용어 추출을 시작합니다.")
    
    # 파일이 없으면 새로 만들고, 있으면 기존 데이터 유지
    if not os.path.exists(DICT_FILE):
        with open(DICT_FILE, "w", encoding="utf-8") as f: json.dump({}, f)

    with pdfplumber.open(PDF_FILE) as pdf:
        for start in range(START_PAGE, END_PAGE + 1, BATCH_SIZE):
            end = min(start + BATCH_SIZE - 1, END_PAGE)
            print(f"\n[진행중] {start}p ~ {end}p 분석 중...")
            
            # 텍스트 추출
            batch_text = ""
            for i in range(start-1, end):
                page_text = pdf.pages[i].extract_text()
                if page_text: batch_text += page_text
            
            # AI 요청
            new_data = get_gemini_response(batch_text)

            if new_data:
                with open(DICT_FILE, "r", encoding="utf-8") as f:
                    master_dict = json.load(f)
                master_dict.update(new_data)
                with open(DICT_FILE, "w", encoding="utf-8") as f:
                    json.dump(master_dict, f, ensure_ascii=False, indent=2)
                print(f"✅ {len(new_data)}개 추가됨! (현재 누적: {len(master_dict)}개)")
            
            # 끝이 아니면 15초 휴식 (무료 할당량 보호)
            if end < END_PAGE:
                print(f"⏳ 다음 작업을 위해 15초간 대기합니다...")
                time.sleep(15)

    print("\n✨ 모든 작업이 완료되었습니다! master_dictionary.json을 확인하세요.")

if __name__ == "__main__":
    run()