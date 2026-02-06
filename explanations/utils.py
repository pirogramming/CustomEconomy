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
                    {"level": 1, "role": "주거 상담사", "description": "전월세 계약이 처음이거나 생애 첫 독립을 준비하는 사회초년생"},
                    {"level": 2, "role": "베테랑 공인중개사", "description": "실거주 목적으로 3~5년 내 이사 경험이 있는 실수요자"},
                    {"level": 3, "role": "부동산 시장 분석가", "description": "1~2채 보유하며 전세가율, 수익률 등을 계산해보는 소액 투자자"},
                    {"level": 4, "role": "부동산 세무/경매 컨설턴트", "description": "다주택자 또는 건물주로 양도세, 종부세 등 세금 전략을 고민하는 투자자"},
                    {"level": 5, "role": "자산운용사 부동산 PF팀", "description": "대규모 개발사업, 리츠 운용 등 기관급 투자를 하는 전문가"}
                ],
                'term_criteria': "Lv1: LTV, 전세가율 등 계약 기초 | Lv2: 실거래가, 호가, 중개수수료 | Lv3: 갭투자, 레버리지, 공시지가 | Lv4: 양도세, 종부세, 취득세 중과 | Lv5: Cap Rate, NPL, REITs, PF대출"
            }
        
        elif category == '기업':
            return {
                'personas': [
                    {"level": 1, "role": "진로 상담사", "description": "중고등학생 또는 대학 저학년으로 기업 이름 정도만 아는 학생"},
                    {"level": 2, "role": "기업 채용 담당자", "description": "취업 준비생으로 연봉, 복지, 회사 성장성에 관심이 많은 구직자"},
                    {"level": 3, "role": "경영기획팀 실무자", "description": "3~5년차 직장인으로 경쟁사 분석, 사업 모델을 이해하는 실무자"},
                    {"level": 4, "role": "산업 전문 기자", "description": "업계 동향, 기술 경쟁력, 시장점유율 변화를 추적하는 분석가"},
                    {"level": 5, "role": "그룹 전략 담당 임원", "description": "M&A, 사업 포트폴리오 재편, 글로벌 전략을 수립하는 경영진"}
                ],
                'term_criteria': "Lv1: 매출, 영업이익, 순이익 | Lv2: 시가총액, 배당, 복지 | Lv3: 영업이익률, BM, 점유율 | Lv4: EBITDA, 밸류에이션, 경쟁우위 | Lv5: M&A, 수직계열화, ESG경영"
            }
        
        elif category == '증권':
            return {
                'personas': [
                    {"level": 1, "role": "주식 초보 멘토", "description": "주식 계좌 개설 후 첫 매수를 고민하는 입문자"},
                    {"level": 2, "role": "5년차 개인투자자", "description": "월 적립식으로 ETF나 우량주에 투자하는 장기 투자자"},
                    {"level": 3, "role": "증권사 리서치 애널리스트", "description": "실적 발표, 재무제표를 보고 기업 가치를 평가하는 투자자"},
                    {"level": 4, "role": "전업 트레이더", "description": "차트 분석, 수급 파악으로 단기 매매하는 기술적 투자자"},
                    {"level": 5, "role": "헤지펀드 매니저", "description": "포트폴리오 리밸런싱, 파생상품 헤지 등을 하는 고액 자산가"}
                ],
                'term_criteria': "Lv1: 매수/매도, 시가/종가, 배당 | Lv2: 시가총액, PER, 배당수익률 | Lv3: PBR, ROE, 컨센서스 | Lv4: 이동평균선, 거래량, 공매도 | Lv5: VIX, Beta, 알파, MSCI편입"
            }
        
        elif category == '경제':
            return {
                'personas': [
                    {"level": 1, "role": "사회 선생님", "description": "경제 뉴스를 처음 접하거나 기초 경제 개념이 필요한 일반인"},
                    {"level": 2, "role": "직장인 경제 해설가", "description": "월급, 물가, 금리 변동이 내 생활에 미치는 영향을 아는 직장인"},
                    {"level": 3, "role": "경제연구소 연구원", "description": "GDP, 환율, 수출입 등 거시지표로 경기를 판단하는 관심층"},
                    {"level": 4, "role": "정책 분석가", "description": "정부 정책이 산업과 사업에 미칠 영향을 분석하는 사업가"},
                    {"level": 5, "role": "경제학 교수", "description": "통화정책, 재정정책의 이론적 배경과 파급효과를 분석하는 전문가"}
                ],
                'term_criteria': "Lv1: 물가, 금리, 실업률 | Lv2: 환율, CPI, 기준금리 | Lv3: GDP, 경상수지, 경제성장률 | Lv4: 재정적자, 국가부채, 기저효과 | Lv5: 통화승수, 필립스곡선, 양적완화"
            }
        
        elif category == '금융':
            return {
                'personas': [
                    {"level": 1, "role": "은행 창구 직원", "description": "예적금, 대출 상품을 처음 알아보는 금융 초보"},
                    {"level": 2, "role": "은행 PB", "description": "재테크에 관심 있는 직장인으로 적금, 펀드 정도를 아는 사람"},
                    {"level": 3, "role": "금융지주 전략팀", "description": "금융권 취업 준비 또는 금융사 실무자로 상품 구조를 이해하는 사람"},
                    {"level": 4, "role": "리스크 관리자", "description": "대출 건전성, NPL 비율 등으로 금융사 안정성을 보는 투자자"},
                    {"level": 5, "role": "금융위원회 정책 자문위원", "description": "금융 규제, 시스템 리스크를 분석하는 규제 전문가"}
                ],
                'term_criteria': "Lv1: 이자, 원금, 신용등급 | Lv2: 적금, 펀드, ISA | Lv3: NIM, 여신, 수신 | Lv4: NPL, BIS비율, 연체율 | Lv5: D-SIB, 바젤III, LCR, 자본적정성"
            }
        
        else:
            return {
                'personas': [
                    {"level": 1, "role": "초보자", "description": "경제 뉴스를 처음 접하는 일반인"},
                    {"level": 2, "role": "중급자", "description": "기초 경제 개념을 아는 관심층"},
                    {"level": 3, "role": "실무자", "description": "업무상 경제 정보가 필요한 직장인"},
                    {"level": 4, "role": "전문가", "description": "해당 분야 실무 경험이 있는 전문가"},
                    {"level": 5, "role": "최고 전문가", "description": "정책 결정이나 전략 수립을 하는 최고 전문가"}
                ],
                'term_criteria': "Lv1: 기초 용어 | Lv2: 일반 용어 | Lv3: 실무 용어 | Lv4: 전문 용어 | Lv5: 고급 전문 용어"
            }

    def generate_single_level_analysis(self, text, category, interests, target_level):
        """
        ⭐ 새로운 메서드: 특정 레벨 1개만 생성 (토큰 최소화)
        """
        
        print(f"🎯 레벨 {target_level} 단독 분석 시작")
        print(f"   카테고리: {category}")
        print(f"   관심사: {interests}")
        print(f"   기사 길이: {len(text)}자")

        if not text or len(text) < 10:
            print("❌ 기사 내용이 너무 짧습니다.")
            return None

        try:
            cat_info = self._get_category_info(category)
            interests_str = ", ".join(interests)
            
            # target_level에 해당하는 페르소나 정보 가져오기
            persona = cat_info['personas'][target_level - 1]
            
            # 프롬프트 (1개 레벨만!)
            prompt = f"""당신은 금융/경제 뉴스를 레벨별로 맞춤 해설하는 전문 AI입니다.

[기사 원문]
{text[:2000]}

[카테고리] {category}
[사용자 관심사] {interests_str}
[타겟 레벨] Level {target_level}
[타겟 페르소나] {persona['role']} - {persona['description']}

[용어 기준]
{cat_info['term_criteria']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 작성 규칙 (레벨 {target_level} 전용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **storytelling**: {persona['description']}에게 맞춰 300~400자로 자연스럽게 설명

2. **terms**: 반드시 2개만 선정
   - 기사 원문이나 storytelling에 나온 용어 중 선택
   - 레벨 {target_level}에 적합한 난이도

3. **advice**: [{interests_str}] 중 기사와 가장 관련 깊은 분야 1개 선택
   - 전망/견해 제시 후 반드시 면책 문구 추가

**JSON 출력 (마크다운 금지):**

{{
  "level": {target_level},
  "role": "{persona['role']}",
  "storytelling": "레벨 {target_level}에 맞는 해설 (300~400자)",
  "terms": [
    {{"term": "용어1", "explanation": "설명1"}},
    {{"term": "용어2", "explanation": "설명2"}}
  ],
  "advice": "관심분야 조언 + 단, 이 전망은 AI 기반 추천이며, 모든 투자 결정과 그에 따른 책임은 본인에게 있습니다."
}}

JSON 객체만 출력. ```json 금지."""

            print("🚀 AI 호출 중...")
            
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 4096,  # 1개 레벨이므로 4K로 충분
                }
            )
            
            print(f"✅ AI 응답 수신 (finish_reason: {response.candidates[0].finish_reason})")
            
            if response.candidates[0].finish_reason == 2:
                print("⚠️ 응답 잘림")
                return None
            
            if not response.parts:
                print("⚠️ 응답 없음")
                return None

            raw_text = response.text.strip()
            
            # JSON 정제
            cleaned = re.sub(r'^```json\s*', '', raw_text, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            print(f"✅ 파싱 성공! Level {target_level} 데이터 생성 완료")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return None
            
        except Exception as e:
            print(f"❌ 에러: {type(e).__name__}: {e}")
            return None