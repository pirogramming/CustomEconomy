import feedparser
import time
import re
import requests
import pytz
import os
import django
from datetime import datetime, timedelta
from dateutil import parser
from bs4 import BeautifulSoup
from newspaper import Article as NewsArticle
from django.utils import timezone

# 1. 프로젝트 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from articles.models import Article, Category
from accounts.models import Interest

class MKNewsFetcher:
    def __init__(self):
        self.rss_map = {
            '경제': 'https://www.mk.co.kr/rss/30100041/',
            '기업': 'https://www.mk.co.kr/rss/50100032/',
            '증권': 'https://www.mk.co.kr/rss/50200011/',
            '부동산': 'https://www.mk.co.kr/rss/50300009/'
        }
        self.popular_rss = 'https://www.mk.co.kr/rss/30000001/'
        self.seoul_tz = pytz.timezone('Asia/Seoul')
        
        # 소분류 맵
        self.category_map = {
            "물가/인플레": ["물가", "인플레이션", "CPI", "소비자물가", "생산자물가", "공공요금", "장바구니", "신선식품", "유가", "기름값", "공급망", "기대인플레이션", "디플레이션", "스태그플레이션", "근원물가"],
            "고용/지표": ["고용", "실업률", "취업자", "경제성장률", "GDP", "GNI", "경기지수", "불황", "경기침체", "R의공포", "비농업고용", "신규실업수당", "OECD성장률", "잠재성장률", "경기선행지수"],
            "환율/외환": ["환율", "달러", "엔화", "위안화", "유로화", "외환", "강달러", "약달러", "킹달러", "엔저", "환전", "통화스왑", "외환보유고", "역외환율", "환율변동", "경상수지", "무역수지"],
            "세금/재정": ["종부세", "상속세", "증여세", "법인세", "소득세", "세수", "추경", "국가채무", "나라살림", "재정적자", "금융투자소득세", "금투세", "세제개편", "연말정산", "절세"],
            "통화/금리": ["기준금리", "연준", "Fed", "한은", "금융통화위원회", "금통위", "금리인상", "금리인하", "동결", "점도표", "파월", "이창용", "베이비스텝", "빅스텝", "자이언트스텝", "긴축", "완화"],
            "은행/대출": ["주담대", "신용대출", "가계부채", "예적금", "금리비교", "시중은행", "인터넷은행", "연체율", "부실채권", "NPL", "여신", "수신", "대출규제", "DSR", "LTV", "DTI", "특례보금자리"],
            "보험/카드": ["실손보험", "자동차보험", "보험료", "카드수수료", "신용카드", "체크카드", "카드포인트", "보장내역", "보험금", "연금보험", "결제액", "리볼빙", "카드론"],
            "가상자산": ["비트코인", "이더리움", "알트코인", "가상화폐", "암호화폐", "블록체인", "거래소", "업비트", "빗썸", "반감기", "현물ETF", "스테이킹", "CBDC", "NFT", "채굴"],
            "국내증시": ["코스피", "코스닥", "KOSPI", "KOSDAQ", "주가", "상장", "상장폐지", "공모주", "IPO", "개미", "동학개미", "외인", "기관", "순매수", "순매도", "공매도", "배당금", "우선주"],
            "해외증시": ["나스닥", "S&P500", "다우지수", "뉴욕증시", "서학개미", "필라델피아반도체", "니케이", "상해종합", "엔비디아", "테슬라", "애플", "마이크로소프트", "매그니피센트7"],
            "채권/상품": ["국채", "채권금리", "수익률", "금값", "원자재", "구리", "천연가스", "WTI", "은값", "안전자산", "위험자산", "ETF", "ETN", "인버스", "레버리지"],
            "반도체": ["삼성전자", "SK하이닉스", "HBM", "반도체", "D램", "NAND", "파운드리", "팹리스", "웨이퍼", "AI반도체", "초미세공정", "TSMC", "인텔", "마이크론", "반도체수출"],
            "자동차/모빌리티": ["현대차", "기아", "전기차", "수소차", "자율주행", "배터리", "이차전지", "양극재", "음극재", "리튬", "캐즘", "에코프로", "포스코홀딩스", "LFP", "NCM"],
            "IT/플랫폼": ["네이버", "카카오", "플랫폼", "AI", "인공지능", "챗GPT", "클라우드", "소프트웨어", "빅테크", "데이터센터", "스타트업", "유니콘", "웹툰", "게임"],
            "실적/경영": ["매출", "영업이익", "당기순이익", "어닝서프라이즈", "어닝쇼크", "흑자", "적자", "M&A", "인수합병", "지배구조", "경영권", "지주사", "구조조정", "ESG"],
            "부동산정책": ["분양가상한제", "규제지역", "투기과열지구", "재건축", "재개발", "공급대책", "그린벨트", "용적률", "건폐율", "신도시", "3기신도시", "안전진단", "공공분양"],
            "매매/분양": ["아파트값", "실거래가", "급매", "청약", "특별공급", "미분양", "집값", "매수심리", "부동산PF", "입주물량", "모델하우스", "청약홈", "당첨자", "프리미엄", "피"],
            "임대차/전세": ["전세", "월세", "전세금", "임대차법", "역전세", "깡통전세", "전세사기", "보증금", "확정일자", "전입신고", "임차인", "임대인", "복비", "중개수수료"]
        }

    def _get_category_by_url(self, url):
        url = url.lower()
        name = None
        if 'stock' in url: name = '증권'
        elif 'business' in url: name = '기업'
        elif 'estate' in url: name = '부동산'
        elif 'finance' in url: name = '금융'
        elif 'economy' in url: name = '경제'
        
        if name:
            category, _ = Category.objects.get_or_create(name=name)
            return category
        return None

    def _analyze_sub_categories(self, content):
        if not content: return []
        counts = {}
        for sub_cat, keywords in self.category_map.items():
            count = sum(content.count(kw) for kw in keywords)
            if count > 0: counts[sub_cat] = count
        if not counts: return []
        max_val = max(counts.values())
        return [cat for cat, count in counts.items() if count == max_val]

    def _clean_content(self, text):
        if not text: return ""
        
        if text.strip().startswith("Key Points"): return None
        lines = text.split('\n')
        cleaned = [l for l in lines if not (l.strip().startswith("사진 확대") or l.strip().startswith("▶") or ("@" in l and "mk.co.kr" in l))]
        return re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned)).strip()

    def _extract_article_date(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            meta = soup.find("meta", {"property": "article:published_time"})
            if meta and meta.get("content"): return parser.parse(meta["content"]).date()
            m = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', soup.get_text())
            if m: return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except: pass
        return None

    def _build_published_at(self, article_date):
        return self.seoul_tz.localize(datetime.combine(article_date, datetime.min.time())) + timedelta(hours=12)

    def update_popular_news(self, limit=5):
        print(f"\n--- [인기뉴스] 최신 {limit}개 갱신 시작 ---")
        Article.objects.filter(is_popular=True).update(is_popular=False)
        feed = feedparser.parse(self.popular_rss)
        success = 0
        skip_reasons = {"중복": 0, "분류불가": 0, "에러": 0, "키포인트제외": 0}

        for entry in feed.entries:
            if success >= limit: break
            actual_category = self._get_category_by_url(entry.link)
            if "[표]" in entry.title or "[포토]" in entry.title:
                print(f"  ⏩ [제목 스킵] {entry.title[:15]}...")
                continue
            if not actual_category:
                skip_reasons["분류불가"] += 1
                continue
            existing_article = Article.objects.filter(url=entry.link).first()
            if existing_article:
                existing_article.is_popular = True
                existing_article.save()
                success += 1
                print(f"  🔥 [인기 갱신] {existing_article.title[:20]}...")
                continue
            try:
                news = NewsArticle(entry.link, language='ko')
                news.download(); news.parse()
                content = self._clean_content(news.text)
                if content is None:
                    skip_reasons["키포인트제외"] += 1
                    continue
                sub_cats = self._analyze_sub_categories(content)
                article_date = self._extract_article_date(entry.link) or parser.parse(entry.published).date()
                article=Article.objects.create(
                    category=actual_category,
                    title=entry.title, 
                    description=entry.description[:200] if entry.description else (news.meta_description[:200] if news.meta_description else ""),
                    content=content, image_url=news.top_image, url=entry.link,
                    source="매일경제", published_at=self._build_published_at(article_date),
                    is_popular=True
                )
                # 분석된 소분류(sub_cats)를 실제 Interest 객체와 연결 (핵심 추가!)
                if sub_cats:
                    from accounts.models import Interest
                    # category_map의 키값과 DB의 Interest 이름이 같아야 합니다.
                    target_interests = Interest.objects.filter(
                        name__in=sub_cats, 
                        category_type='SUB'
                    )
                    article.sub_interests.add(*target_interests)

                success += 1
                print(f"  🔥 [인기 신규] {entry.title[:20]}...")
                time.sleep(0.3)
            except: skip_reasons["에러"] += 1
        print(f"✨ 인기 완료: {success}/{limit} (스킵이유: {skip_reasons})")

    def run_import(self, category_name, limit=3):
        target_url = self.rss_map.get(category_name)
        feed = feedparser.parse(target_url)
        success = 0
        skip_reasons = {"중복": 0, "분류불가": 0, "에러": 0, "키포인트제외": 0}
        print(f"\n--- [{category_name}] 수집 시작 (목표: {limit}개) ---")

        for entry in feed.entries:
            if success >= limit: break
            if "[표]" in entry.title or "[포토]" in entry.title:
                print(f"  ⏩ [제목 스킵] {entry.title[:15]}...")
                continue
            actual_category = self._get_category_by_url(entry.link)
            if not actual_category:
                skip_reasons["분류불가"] += 1
                continue
            if Article.objects.filter(url=entry.link).exists():
                skip_reasons["중복"] += 1
                continue
            try:
                news = NewsArticle(entry.link, language='ko')
                news.download(); news.parse()
                if "[표]" in news.title or "[포토]" in news.title:
                    print(f"  ⏩ [제목 스킵] {news.title[:15]}...")
                    continue
                content = self._clean_content(news.text)
                if content is None:
                    skip_reasons["키포인트제외"] += 1
                    continue
                sub_cats = self._analyze_sub_categories(content)
                article_date = self._extract_article_date(entry.link) or parser.parse(entry.published).date()
                article=Article.objects.create(
                    category=actual_category,
                    title=entry.title, 
                    description=entry.description[:200] if entry.description else (news.meta_description[:200] if news.meta_description else ""),
                    content=content, image_url=news.top_image,
                    url=entry.link, source="매일경제", is_popular=False,
                    published_at=self._build_published_at(article_date)
                )
                # 분석된 소분류(sub_cats)를 실제 Interest 객체와 연결 (핵심 추가!)
                if sub_cats:
                    from accounts.models import Interest
                    # category_map의 키값과 DB의 Interest 이름이 같아야 합니다.
                    target_interests = Interest.objects.filter(
                        name__in=sub_cats, 
                        category_type='SUB'
                    )
                    article.sub_interests.add(*target_interests)

                success += 1
                print(f"  ✅ [일반][{actual_category.name}] 소분류:{sub_cats} | {entry.title[:15]}...")
                time.sleep(0.3)
            except: skip_reasons["에러"] += 1
        print(f"  ⚠️ 요약: {success}/{limit} 저장 (스킵이유: {skip_reasons})")

    def fetch_financial_links(self, limit=15):
        url = "https://www.mk.co.kr/news/financial/"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = soup.select("a.link_style4, a.link_style_list, a.link_style2, a.link_style1")
            links = []
            for tag in tags:
                link = tag.get('href')
                if link and link.startswith('/'): link = f"https://www.mk.co.kr{link}"
                if link and link not in links: links.append(link)
                if len(links) >= limit: break
            return links
        except: return []

    def run_import_from_links(self, category_name, links, limit=5):
        category, _ = Category.objects.get_or_create(name=category_name)
        success = 0
        skip_reasons = {"중복": 0, "키포인트제외": 0, "에러": 0}
        print(f"\n--- [{category_name}] 수집 시작 (목표: {limit}개) ---")

        for link in links:
            if success >= limit: break
            if Article.objects.filter(url=link).exists():
                skip_reasons["중복"] += 1
                continue
            try:
                news = NewsArticle(link, language='ko')
                news.download(); news.parse()
                content = self._clean_content(news.text)
                if "[표]" in news.title or "[포토]" in news.title:
                    print(f"  ⏩ [제목 스킵] {news.title[:15]}...")
                    continue
                if content is None:
                    skip_reasons["키포인트제외"] += 1
                    continue
                sub_cats = self._analyze_sub_categories(content)
                article_date = self._extract_article_date(link) or timezone.now().date()
                article=Article.objects.create(
                    category=category,
                    title=news.title, 
                    description=news.meta_description[:200] if news.meta_description else "",
                    content=content, image_url=news.top_image,
                    url=link, source="매일경제", published_at=self._build_published_at(article_date)
                )
                # 분석된 소분류(sub_cats)를 실제 Interest 객체와 연결 (핵심 추가!)
                if sub_cats:
                    from accounts.models import Interest
                    # category_map의 키값과 DB의 Interest 이름이 같아야 합니다.
                    target_interests = Interest.objects.filter(
                        name__in=sub_cats, 
                        category_type='SUB'
                    )
                    article.sub_interests.add(*target_interests)

                success += 1
                print(f"  ✅ [일반][{category_name}] 소분류:{sub_cats} | {news.title[:15]}...")
                time.sleep(0.3)
            except: skip_reasons["에러"] += 1
        print(f"  ⚠️ 요약: {success}/{limit} 저장 (스킵이유: {skip_reasons})")

def start_forever():
    fetcher = MKNewsFetcher()
    interval = 3 * 60 * 60 
    while True:
        try:
            print(f"\n--- [ {datetime.now().strftime('%H:%M:%S')} ] 사이클 시작 ---")
            fetcher.update_popular_news(limit=5)
            for cat in fetcher.rss_map.keys():
                fetcher.run_import(cat, limit=5)
            f_links = fetcher.fetch_financial_links(limit=15)
            fetcher.run_import_from_links('금융', f_links, limit=5)
            print(f"\n✨ 모든 수집 완료! {interval//3600}시간 대기...")
        except Exception as e:
            print(f"🚨 오류: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    start_forever()