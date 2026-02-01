import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiFinancialTutor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ API Key가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def _get_category_info(self, category):
        """카테고리별 페르소나와 용어 기준 반환"""
        
        if category == '부동산':
            return {
                'personas': [
                    {"level": 1, "role": "주거 상담사", "target": "사회초년생"},
                    {"level": 2, "role": "베테랑 공인중개사", "target": "실거주자"},
                    {"level": 3, "role": "부동산 시장 분석가", "target": "소액 투자자"},
                    {"level": 4, "role": "부동산 세무/경매 컨설턴트", "target": "다주택자/건물주"},
                    {"level": 5, "role": "자산운용사 부동산 PF", "target": "기관 투자자"}
                ],
                'terms': "Lv.1~2: LTV, 전세가율 등 기초용어 / Lv.3~4: 조정대상지역, 양도세, 용적률 / Lv.5: Cap Rate, PF 브릿지론, EOD"
            }
        
        elif category == '기업':
            return {
                'personas': [
                    {"level": 1, "role": "진로 상담사", "target": "학생"},
                    {"level": 2, "role": "기업 채용 담당자", "target": "취준생"},
                    {"level": 3, "role": "경영기획팀 실무자", "target": "직장인"},
                    {"level": 4, "role": "산업 전문 기자", "target": "업계 종사자"},
                    {"level": 5, "role": "그룹 전략 담당 임원", "target": "경영진"}
                ],
                'terms': "Lv.1~2: 매출, 영업이익, 복지 / Lv.3~4: BM, 점유율, 카니발라이제이션 / Lv.5: 수직계열화, 밸류체인, ESG 택소노미"
            }
        
        elif category == '증권':
            return {
                'personas': [
                    {"level": 1, "role": "주식 초보 멘토", "target": "주식 입문자"},
                    {"level": 2, "role": "5년차 투자자", "target": "적립식 투자자"},
                    {"level": 3, "role": "증권사 연구원", "target": "실적 분석 투자자"},
                    {"level": 4, "role": "전업 트레이더", "target": "기술적 투자자"},
                    {"level": 5, "role": "헤지펀드 매니저", "target": "고액 자산가"}
                ],
                'terms': "Lv.1~2: 매수/매도, 배당금, 시가총액 / Lv.3: PER, PBR, 컨센서스 / Lv.4: 공매도, 대차잔고 / Lv.5: VIX, Beta, MSCI 리밸런싱"
            }
        
        elif category == '경제':
            return {
                'personas': [
                    {"level": 1, "role": "사회 선생님", "target": "일반 성인"},
                    {"level": 2, "role": "경제 전문가", "target": "직장인"},
                    {"level": 3, "role": "경제연구소 연구원", "target": "경제 관심층"},
                    {"level": 4, "role": "정책 분석가", "target": "사업자"},
                    {"level": 5, "role": "경제학 교수", "target": "전문가"}
                ],
                'terms': "Lv.1~2: 인플레이션, 금리, 최저임금 / Lv.3~4: GDP, CPI, 경상수지 / Lv.5: 통화승수, 재정정책, 필립스 곡선"
            }
        
        elif category == '금융':
            return {
                'personas': [
                    {"level": 1, "role": "은행 창구 직원", "target": "일반 성인"},
                    {"level": 2, "role": "은행 PB", "target": "직장인"},
                    {"level": 3, "role": "금융지주 전략팀", "target": "금융권 실무자"},
                    {"level": 4, "role": "리스크 관리자", "target": "투자자"},
                    {"level": 5, "role": "금융위 자문위원", "target": "규제 전문가"}
                ],
                'terms': "Lv.1~2: 예금이자, 신용등급 / Lv.3~4: NIM, PLCC, BIS비율 / Lv.5: D-SIB, 바젤III, LCR"
            }
        
        else:
            return {
                'personas': [
                    {"level": 1, "role": "초보자", "target": "일반인"},
                    {"level": 2, "role": "중급자", "target": "관심층"},
                    {"level": 3, "role": "실무자", "target": "실무자"},
                    {"level": 4, "role": "전문가", "target": "전문가"},
                    {"level": 5, "role": "최고 전문가", "target": "최고 전문가"}
                ],
                'terms': "Lv.1~2: 기초 용어 / Lv.3~4: 중급 용어 / Lv.5: 전문 용어"
            }

    def generate_analysis(self, text, category, interests):
        """AI 분석 실행 후 Python List 반환"""
        
        print("=" * 60)
        print(f"📡 [AI 분석 시작]")
        print(f"   카테고리: {category}")
        print(f"   관심사: {interests}")
        print(f"   기사 길이: {len(text)}자")
        print("=" * 60)

        if not text or len(text) < 10:
            print("❌ 기사 내용이 너무 짧습니다.")
            return []

        try:
            # 카테고리 정보 가져오기
            cat_info = self._get_category_info(category)
            interests_str = ", ".join(interests)
            
            # 프롬프트 생성
            prompt = f"""당신은 금융/경제 뉴스 해설 전문 AI입니다.

뉴스 카테고리: {category}
사용자 관심사: {interests_str}

[기사 원문]
{text}

[페르소나 정보]
{json.dumps(cat_info['personas'], ensure_ascii=False, indent=2)}

[용어 선정 기준]
{cat_info['terms']}

[작성 규칙]
1. storytelling: 400~500자 분량으로 자연스러운 구어체 해설
2. terms: 레벨에 맞는 용어 2~3개 선정하여 설명 (어려운 용어가 없으면 "특별히 참고할 용어 없음")
3. advice: 사용자 관심사와 연결한 조언 + "단, 해당 전망은 AI 기반 추천이므로 책임은 본인에게 있습니다." 문구 필수

**아래 JSON 형식으로만 출력하세요. 마크다운이나 추가 설명 금지:**

[
  {{
    "level": 1,
    "role": "{cat_info['personas'][0]['role']}",
    "storytelling": "여기에 400~500자 해설",
    "terms": [
      {{"term": "용어1", "explanation": "설명1"}},
      {{"term": "용어2", "explanation": "설명2"}}
    ],
    "advice": "관심사 기반 조언 + 면책 문구"
  }},
  {{
    "level": 2,
    "role": "{cat_info['personas'][1]['role']}",
    "storytelling": "...",
    "terms": [...],
    "advice": "..."
  }},
  {{
    "level": 3,
    "role": "{cat_info['personas'][2]['role']}",
    "storytelling": "...",
    "terms": [...],
    "advice": "..."
  }},
  {{
    "level": 4,
    "role": "{cat_info['personas'][3]['role']}",
    "storytelling": "...",
    "terms": [...],
    "advice": "..."
  }},
  {{
    "level": 5,
    "role": "{cat_info['personas'][4]['role']}",
    "storytelling": "...",
    "terms": [...],
    "advice": "..."
  }}
]

중요: JSON 배열만 출력. ```json 같은 마크다운 절대 금지."""

            print("🚀 AI 호출 중...")
            
            # API 호출
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            
            # 응답 확인
            print(f"✅ AI 응답 수신")
            print(f"   finish_reason: {response.candidates[0].finish_reason}")
            
            if response.prompt_feedback.block_reason:
                print(f"⚠️ 차단됨: {response.prompt_feedback.block_reason}")
                return []
            
            if not response.parts:
                print("⚠️ 응답 내용 없음")
                return []

            # 텍스트 추출
            raw_text = response.text.strip()
            print(f"   응답 길이: {len(raw_text)}자")
            
            # JSON 정제 (마크다운 코드블록 제거)
            cleaned = raw_text
            
            # ```json ... ``` 형식 제거
            cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            
            # JSON 파싱
            print("🔄 JSON 파싱 시도...")
            data = json.loads(cleaned)
            
            print(f"✅ 파싱 성공! {len(data)}개 레벨 데이터 생성")
            
            # 데이터 검증
            for item in data:
                if not all(key in item for key in ['level', 'role', 'storytelling', 'terms', 'advice']):
                    print(f"⚠️ Level {item.get('level', '?')} 데이터 구조 불완전")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"   문제 위치: line {e.lineno}, column {e.colno}")
            print(f"   원본 텍스트 (처음 500자):")
            print(f"   {cleaned[:500]}")
            return []
            
        except Exception as e:
            print(f"❌ 에러 발생: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []