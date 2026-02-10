import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

class GeminiFinancialTutor:
    def __init__(self):
        load_dotenv(override=True)       
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

    def generate_full_analysis_with_all_interests(self, text, category, target_level, all_interests):
        """
        ⭐ 핵심 메서드: 해설 + 8개 관심사 전망을 1회 AI 호출로 생성
        
        Args:
            text: 기사 본문
            category: 기사 카테고리
            target_level: 레벨 (1~5)
            all_interests: 전체 관심사 리스트
                ['투자', '부동산', '대출/금융', '소비', '해외/환율', '세금/정책', '자영업/사업자', '취업/고용']
        
        Returns:
            {
                "storytelling": "...",
                "terms": [...],
                "predictions": {
                    "투자": "투자 전망...",
                    "부동산": "부동산 전망...",
                    ...
                }
            }
        """
        
        print(f"🎯 레벨 {target_level} 전체 분석 시작")
        print(f"   카테고리: {category}")
        print(f"   관심사 개수: {len(all_interests)}개")
        print(f"   기사 길이: {len(text)}자")

        if not text or len(text) < 10:
            print("❌ 기사 내용이 너무 짧습니다.")
            return None

        try:
            cat_info = self._get_category_info(category)
            persona = cat_info['personas'][target_level - 1]
            
            # 레벨별 글자 수 제한
            char_limits = {1: "250~300자", 2: "300~350자", 3: "350~400자", 4: "400~450자", 5: "450~500자"}
            char_limit = char_limits.get(target_level, "400자")
            
            # 관심사 목록 문자열
            interests_str = ", ".join(all_interests)
            
            # JSON 템플릿 동적 생성
            predictions_template = ",\n    ".join([
                f'"{interest}": "{interest} 관점 전망 (4~5문장) + 면책문구"'
                for interest in all_interests
            ])
            
            # 🔥 프롬프트: 8개 관심사 전망 전부 요청
            prompt = f"""당신은 금융/경제 뉴스를 레벨별로 맞춤 해설하는 전문 AI입니다.

[기사 원문]
{text[:2000]}

[카테고리] {category}
[타겟 레벨] Level {target_level}
[타겟 페르소나] {persona['role']} - {persona['description']}

[관심분야 목록]
{interests_str}

[용어 기준]
{cat_info['term_criteria']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 작성 규칙 (레벨 {target_level} 전용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**중요: 작성 톤 & 보이스**
- 타겟 페르소나({persona['role']})는 독자의 **지식 수준을 가늠하는 기준**일 뿐입니다
- 실제 텍스트에서는 독자를 특정 직업/역할로 호칭하거나 지칭하지 마세요
- 예시: "5년차 개인투자자님", "베테랑 공인중개사로서", "경제연구소 연구원이라면" 등 **절대 금지**
- 대신 중립적이고 포괄적인 표현 사용: "투자에 관심 있는 분들", "부동산 시장을 주시하는 분들", "경제 흐름을 파악하고자 하는 분들"
- 설명은 "{persona['description']}" 수준의 배경지식을 전제로 작성하되, 누구나 읽을 수 있는 객관적 톤 유지

1. **storytelling**: 레벨 {target_level} 독자를 위해 {char_limit}로 간결하고 핵심만 설명
   - 독자를 특정 직업으로 호칭하지 말 것 (예: "5년차 개인투자자님" 금지)
   - "{persona['description']}" 수준의 지식을 가진 일반 독자를 대상으로 작성
   - "~님", "투자자님" 등 특정 호칭 사용 금지

2. **terms**: 반드시 2개만 선정
   - 기사 원문이나 storytelling에 나온 용어 중 선택
   - 레벨 {target_level}에 적합한 난이도
   - 각 용어 설명은 2~3문장으로 간결하게

3. **predictions**: 위 [관심분야 목록]의 **8개 항목 각각**에 대해 전망 작성
   - 각 관심사별로 **4~5문장**으로 구체적이고 실질적인 분석 제공
   - 구조: ① 기사의 핵심 내용이 해당 분야에 미치는 영향 (1문장) → ② 구체적 예시나 시나리오 (1~2문장) → ③ 주의할 점이나 대응 방안 (1문장) → ④ 면책문구
   - 기사와 관련이 적은 분야도 간접적 영향, 참고사항, 또는 전반적 경제 흐름과의 연계성을 구체적으로 언급
   - 키(Key)는 반드시 위 목록의 한글 명칭을 **정확히** 사용
   - **톤**: 중립적이고 객관적으로 작성. "~하시는 분", "투자자분들", "사업자님" 등 특정 독자 지칭 금지
   - 모든 전망 끝에 면책 문구 추가: "단, 이 전망은 AI 기반 추천이며, 모든 투자 결정과 그에 따른 책임은 본인에게 있습니다."

**중요**: 
- predictions는 반드시 8개 항목 모두 포함
- 각 전망은 4~5문장으로 충분히 구체적으로 작성
- 단순 나열이 아닌 논리적 흐름으로 구성
- **모든 텍스트는 중립적·객관적 톤 유지 (특정 직업/역할 호칭 절대 금지)**

**JSON 출력 (마크다운 금지):**

{{
  "level": {target_level},
  "role": "{persona['role']}",
  "storytelling": "레벨 {target_level} 해설 ({char_limit}) - 중립적이고 객관적인 톤으로 작성",
  "terms": [
    {{"term": "용어1", "explanation": "간결한 설명 (2~3문장)"}},
    {{"term": "용어2", "explanation": "간결한 설명 (2~3문장)"}}
  ],
  "predictions": {{
    {predictions_template}
  }}
}}

**출력 형식**: JSON 객체만 출력. ```json 마크다운 금지.
**톤 체크리스트**: 
- ❌ "5년차 개인투자자님", "베테랑 공인중개사로서" 
- ✅ "주식 투자를 고려하는 경우", "부동산 시장 동향에 주목할 필요"
"""

            print("🚀 AI 호출 중 (8개 전망 포함)...")
            
            # 🔥 토큰 증가: 4~5문장으로 늘어났으므로 토큰 상향
            token_limits = {
                1: 6144,   # 기존 4096 → 6144
                2: 7168,   # 기존 5120 → 7168
                3: 8192,   # 기존 6144 → 8192
                4: 10240,  # 기존 8192 → 10240
                5: 12288   # 기존 8192 → 12288
            }
            max_tokens = token_limits.get(target_level, 10240)
            print(f"   📊 할당 토큰: {max_tokens}")
            
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": max_tokens,
                }
            )
            
            print(f"✅ AI 응답 수신 (finish_reason: {response.candidates[0].finish_reason})")
            
            if response.candidates[0].finish_reason == 2:
                print(f"⚠️ 응답 잘림! 토큰 부족 (현재: {max_tokens})")
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
            
            # 검증: predictions가 dict이고 8개 항목이 있는지 확인
            predictions = data.get('predictions', {})
            if not isinstance(predictions, dict):
                print("⚠️ predictions가 dict가 아닙니다")
                return None
            
            missing = [i for i in all_interests if i not in predictions]
            if missing:
                print(f"⚠️ 누락된 관심사: {missing}")
                # 누락된 것들은 기본값으로 채움
                for interest in missing:
                    predictions[interest] = "전망 정보를 생성하지 못했습니다. 단, 이 전망은 AI 기반 추천이며, 모든 투자 결정과 그에 따른 책임은 본인에게 있습니다."
            
            print(f"✅ 파싱 성공! Level {target_level} + 8개 전망 생성 완료")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"   원본: {raw_text[:300]}...")
            return None
            
        except Exception as e:
            print(f"❌ 에러: {type(e).__name__}: {e}")
            return None


    def select_best_interest_from_user_list(self, text, user_interests):
        """
        🤖 사용자 관심사 중 기사와 가장 관련 깊은 것 선택
        
        Args:
            text: 기사 본문
            user_interests: 사용자 관심사 리스트
                예: ["투자", "부동산", "소비"]
        
        Returns:
            {
                "selected_interest": "투자",
                "reason": "코스피 지수와 직접 관련",
                "display_text": "관심분야: [투자]"
            }
        """
        
        if not user_interests or len(user_interests) == 0:
            return {
                "selected_interest": "투자", 
                "reason": "기본값",
                "display_text": "관심분야: [투자]"
            }
        
        # 관심사가 1개면 바로 반환
        if len(user_interests) == 1:
            return {
                "selected_interest": user_interests[0], 
                "reason": "유일한 관심사",
                "display_text": f"관심분야: [{user_interests[0]}]"
            }
        
        print(f"🤖 AI에게 최적 관심사 선택 요청...")
        print(f"   후보: {user_interests}")
        
        try:
            interests_str = ", ".join(user_interests)
            
            prompt = f"""당신은 금융/경제 기사를 분석하는 전문가입니다.

[기사 원문]
{text[:1500]}

[사용자의 관심 분야]
{interests_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 작업: 이 기사와 가장 밀접한 관심사 1개 선택
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 관심사 중 이 기사와 **가장 관련성이 높은 1개**를 선택하고,
이유를 1문장으로 간단히 설명하세요.

**중요**: 
- selected_interest는 반드시 위 목록 중 하나를 그대로 사용
- display_text는 "관심분야: [선택된 관심사]" 형식으로 작성

**JSON 출력:**

{{
  "selected_interest": "선택된 관심사",
  "reason": "선택 이유 (1문장)",
  "display_text": "관심분야: [선택된 관심사]"
}}

예시:
{{
  "selected_interest": "투자",
  "reason": "코스피 지수 급등과 직접 관련",
  "display_text": "관심분야: [투자]"
}}

JSON만 출력. ```json 금지."""

            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 20,
                    "max_output_tokens": 256,
                }
            )
            
            if response.candidates[0].finish_reason != 1:
                return {
                    "selected_interest": user_interests[0], 
                    "reason": "AI 실패",
                    "display_text": f"관심분야: [{user_interests[0]}]"
                }
            
            raw_text = response.text.strip()
            cleaned = re.sub(r'^```json\s*', '', raw_text, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            # 검증
            selected = data.get('selected_interest', '')
            if selected not in user_interests:
                print(f"⚠️ AI가 잘못된 관심사 반환: {selected}")
                return {
                    "selected_interest": user_interests[0], 
                    "reason": "검증 실패",
                    "display_text": f"관심분야: [{user_interests[0]}]"
                }
            
            # display_text가 없으면 생성
            if 'display_text' not in data:
                data['display_text'] = f"관심분야: [{selected}]"
            
            print(f"✅ AI 선택: {selected}")
            return data
            
        except Exception as e:
            print(f"❌ 에러: {e}")
            return {
                "selected_interest": user_interests[0], 
                "reason": "에러",
                "display_text": f"관심분야: [{user_interests[0]}]"
            }