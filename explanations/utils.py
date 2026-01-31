import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from django.conf import settings

class GeminiFinancialTutor:
    def __init__(self):
        # settings.py 또는 .env에서 API 키 로드
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # 로컬 테스트용 하드코딩 (배포 시 삭제 요망) 또는 에러 처리
            print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-flash-preview') # 최신 모델 사용 권장
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def _get_json_prompt(self, news_category_1, text, user_interests):
        """
        AI에게 JSON 형식의 출력을 요청하는 프롬프트 생성
        """
        interests_str = ", ".join(user_interests)

        # -------------------------------------------------------------
        # 카테고리별 페르소나 및 기준 (형님의 new_main_system.py 로직 이식)
        # -------------------------------------------------------------
        # 1. 부동산 (Estate)
        if news_category_1 == '부동산':
            personas = """
            1. [Lv.1 주거 상담사] (대상: 사회초년생)
            2. [Lv.2 베테랑 공인중개사] (대상: 실거주자)
            3. [Lv.3 부동산 시장 분석가] (대상: 소액 투자자)
            4. [Lv.4 부동산 세무/경매 컨설턴트] (대상: 다주택자 / 건물주)
            5. [Lv.5 자산운용사 부동산 PF] (대상: 기관 투자자)
            """
            term_criteria = """
            - Lv.1~2: LTV(대출한도), 전세가율 등 기초 용어 풀이.
            - Lv.3~4: '조정대상지역', '양도세 중과배제', '용적률' 등 정책 및 세무 용어 중심.
            - Lv.5: 'Cap Rate(자본환원율)', 'PF 브릿지론', 'EOD(기한이익상실)' 등 전문가용 금융/개발 용어 선정.
            """

        # 2. 기업 (Corp)
        elif news_category_1 == '기업':
            personas = """
            1. [Lv.1 진로 상담사] (대상: 학생)
            2. [Lv.2 기업 채용 담당자] (대상: 취준생 / 회사 성장성 및 복지)
            3. [Lv.3 경영기획팀 실무자] (대상: 직장인 / 경쟁사 비교 및 BM 분석)
            4. [Lv.4 산업 전문 기자] (대상: 업계 종사자 / 기술 격차 및 점유율)
            5. [Lv.5 그룹 전략 담당 임원(CSO)] (대상: 경영진 / M&A 및 생존 전략)
            """
            term_criteria = """
            - Lv.1~2: '매출', '영업이익', '복지' 등 기초 개념.
            - Lv.3~4: 'BM(비즈니스모델)', '점유율', '카니발라이제이션' 등 경영 전략 용어.
            - Lv.5: '수직계열화', '밸류체인', 'PoC', 'ESG 택소노미' 등 경영층/전략 용어 선정.
            """

        # 3. 증권 (Stock) - 투자 관점
        elif news_category_1 == '증권':
            personas = """
            1. [Lv.1 주식 초보 멘토] (대상: 주식 입문자)
            2. [Lv.2 5년이상 주식을 한 직장인] (대상: 적립식 투자자 / ETF 관심)
            3. [Lv.3 증권사 리서치센터 연구원] (대상: 실적 분석이 가능한 투자자)
            4. [Lv.4 전업 트레이더] (대상: 차트와 수급을 보는 기술적 투자자)
            5. [Lv.5 헤지펀드 펀드매니저] (대상: 고액 자산가)
            """
            term_criteria = """
            - Lv.1~2: '매수/매도', '배당금', '시가총액' 등 주식 기초 용어.
            - Lv.3: 'PER', 'PBR', '컨센서스', '어닝 서프라이즈' 등 밸류에이션 용어.
            - Lv.4: '공매도', '대차잔고', '골든크로스', '선물/옵션' 등 수급 및 파생 용어.
            - Lv.5: '변동성(VIX)', '베타(Beta)', 'MSCI 리밸런싱' 등 포트폴리오 관리 용어 선정.
            """

        # 4. 경제 (Economy) - 거시경제/정책 관점 - 이론 중심
        elif news_category_1 == '경제':
            personas = """
            1. [Lv.1 사회 선생님] (대상: 경제활동이 가능한 성인)
            2. [Lv.2 경제활동을 5년이상 한 직장인을 위한 경제 전문가 ] (대상:직장인)
            3. [Lv.3 경제연구소 연구원] (대상: 경제 흐름을 읽고 싶은 사람)
            4. [Lv.4 정책 분석가] (대상: 정부 정책의 영향을 받는 사업자)
            5. [Lv.5 경제학 교수] (대상: 경제 전망을 위한 전문가)
            """
            term_criteria = """
            - Lv.1~2: '인플레이션(물가상승)', '금리', '최저임금' 등 체감 경제 용어.
            - Lv.3~4: 'GDP', 'CPI(소비자물가)', '경상수지', '기저효과' 등 거시 지표 용어.
            - Lv.5: '통화승수', '재정정책', '양적완화/긴축', '필립스 곡선' 등 학술/정책 용어 선정.
            """

        # 5. 금융 (Finance) - 은행/보험/핀테크 관점 - 돈의 흐름
        elif news_category_1 == '금융':
            personas = """
            1. [Lv.1 은행 창구 직원] (대상: 경제활동이 가능한 성인)
            2. [Lv.2 은행 PB] (대상: 직장인)
            3. [Lv.3 금융지주 전략팀] (대상: 금융권 취준생/실무자)
            4. [Lv.4 리스크 관리자] (대상: 대출 건전성을 보는 투자자)
            5. [Lv.5 금융위원회 정책 자문위원] (대상: 금융 규제 및 시스템 전문가)
            """
            term_criteria = """
            - Lv.1~2: '예금이자', '신용등급', '마이너스통장' 등 생활 금융 용어.
            - Lv.3~4: 'NIM(순이자마진)', 'PLCC', '연체율', 'BIS비율' 등 금융사 수익성/건전성 용어.
            - Lv.5: 'D-SIB(시스템적 중요 은행)', '바젤III', '유동성커버리지비율(LCR)', 'PF 리스크' 등 규제 용어 선정.
            """
        
        # 예외 처리 (혹시 모를 오류 방지)
        else:
            personas = "1. [Lv.1 초보자]\n5. [Lv.5 전문가]"
            term_criteria = "- Lv.1: 기초 용어\n- Lv.5: 심화 용어"

        # -------------------------------------------------------------
        # JSON 강제 프롬프트
        # -------------------------------------------------------------
        return f"""
        당신은 금융/경제 뉴스 해설 AI입니다.
        뉴스 카테고리: {news_category_1}
        사용자 관심사: {interests_str}

        [뉴스 원문]
        {text}

        [분석해야 할 5가지 페르소나]
        {personas}

        [작성 가이드라인]
        1. **스토리텔링**: 각 역할(Persona)이 청중에게 말하듯이 자연스러운 구어체로 설명하세요 (분량: 400~500자 유동적).
        2. **용어 선정 기준 (Strict)**: 아래 기준을 반드시 따르세요.
        {term_criteria}
        *주의: Lv.5에서 전문가도 모를 만한 난해한 용어가 본문에 없다면, 억지로 설명하지 말고 "전문가가 특별히 참고할 난해한 용어는 없습니다."라고 출력하세요.*
        
        3. **맞춤 조언**: 마지막 섹션에서 사용자의 관심사 **[{interests_str}]** 와 이 뉴스를 연결지어 조언하세요.
           (관심사가 여러 개면, 기사 내용과 가장 연관성 높은 1개를 골라 집중 조언)

        [⭐⭐ 필수 출력 형식 (엄수) ⭐⭐]
        각 레벨마다 아래 포맷을 그대로 유지하세요.

        === [Lv.N 역할명] ===
        🎙️ **[기사 스토리텔링]**: (본문 해설)
        💡 **[용어 돋보기]**: (기준에 맞춘 용어 2~3개 풀이)
        🔮 **[맞춤 전망: {interests_str}]**: 
           (사용자 관심사에 따른 조언)
           "단, 해당 전망은 AI의 성능 기반의 단순 추천이므로 모든 선택에 대한 책임은 본인에게 있음을 알려드립니다."
        """

    def generate_analysis(self, text, category, interests):
        """
        AI 분석 실행 후 Python List(JSON) 반환
        """
        try:
            prompt = self._get_json_prompt(category, text, interests)
            # print(f"🤖 AI 분석 요청 중... (카테고리: {category})")
            
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            
            # 응답 데이터 정제 (Markdown 코드블럭 제거)
            raw_text = response.text.strip()
            cleaned_text = re.sub(r'^```json\s*|\s*```$', '', raw_text, flags=re.MULTILINE)
            
            # JSON 파싱
            return json.loads(cleaned_text)
            
        except Exception as e:
            print(f"❌ AI 분석 중 에러 발생: {e}")
            # 에러 발생 시 빈 리스트 반환하여 서버 다운 방지
            return []