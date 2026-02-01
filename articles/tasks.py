import feedparser
import time
import re
from datetime import datetime
from dateutil import parser
from newspaper import Article as NewsArticle
from .models import Article, Category
import requests
from bs4 import BeautifulSoup

class MKNewsFetcher:
    def __init__(self):
        self.rss_map = {
            '경제': 'https://www.mk.co.kr/rss/30100041/',
            '기업': 'https://www.mk.co.kr/rss/50100032/',
            '증권': 'https://www.mk.co.kr/rss/50200011/',
            '부동산': 'https://www.mk.co.kr/rss/50300009/'
        }
        self.popular_rss = 'https://www.mk.co.kr/rss/30000001/'

    def _clean_content(self, text):
        if not text: return ""
        lines = text.split('\n')
        
        cleaned_lines = []
        for l in lines:
            if not (l.strip().startswith("사진 확대") or l.strip().startswith("▶") or ("@" in l and "mk.co.kr" in l)):
                cleaned_lines.append(l)
        
        cleaned_text = '\n'.join(cleaned_lines)
        return re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()

    def fetch_financial_links(self, limit=5):
        url="https://www.mk.co.kr/news/financial/"
        headers={'User-Agent':"Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers)
            soup=BeautifulSoup(response.text, 'html.parser')

            selectors = "a.link_style4, a.link_style_list, a.link_style2, a.linke_style1"
            found_tags = soup.select(selectors)

            links=[]
            for tag in found_tags:
                link = tag.get('href')
                if link and link.startswith('/'):
                    link = f"https://www.mk.co.kr{link}"
                if link and link not in links:
                    links.append(link)
                if len(links) >= limit:
                    break
            return links
        except Exception as e:
            print(f"❌ 금융 페이지 접속 실패: {e}")
            return []

    def run_import_from_links(self, category_name, links):
        category_obj, _ = Category.objects.get_or_create(name=category_name)
        count = 0

        for link in links:
            if Article.objects.filter(url=link).exists():
                print(f"이미 있는 기사라 패스: {link}")
                continue

            try:
                news = NewsArticle(link, language='ko')
                news.download()
                news.parse()

                cleaned_content = self._clean_content(news.text)
                if cleaned_content.strip().startswith("Key Points"):
                    print(f"Key Points 기사라 패스: {link}")
                    continue

                pub_date = news.publish_date if news.publish_date else datetime.now()

                Article.objects.create(
                    category=category_obj,
                    title=news.title,
                    description=news.meta_description[:200] if news.meta_description else "",
                    content = cleaned_content,
                    image_url = news.top_image,
                    url = link,
                    source = "매일경제",
                    published_at =pub_date
                )
                count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ 저장 실패: {link} ({e})")
        return count

    def run_import(self, category_name, limit=5):
        target_url = self.rss_map.get(category_name, self.popular_rss)
        feed = feedparser.parse(target_url)

        category_obj, _ = Category.objects.get_or_create(name=category_name)
        count = 0

        for entry in feed.entries[:limit]: 
            if Article.objects.filter(url=entry.link).exists():
                continue

            try:
                news = NewsArticle(entry.link, language='ko')
                news.download()
                news.parse()

                cleaned_content = self._clean_content(news.text)
                if cleaned_content.strip().startswith("Key Points"):
                    print(f"⏩ 건너뜀: 'Key Points'로 시작하는 기사 ({entry.title[:10]}...)")
                    continue
                
                pub_date = parser.parse(entry.published)

                Article.objects.create(
                    category=category_obj,
                    title=entry.title, 
                    description=entry.description[:200] if entry.description else "", 
                    content=self._clean_content(news.text),
                    image_url=news.top_image,
                    url=entry.link,
                    source="매일경제",
                    published_at=pub_date
                )
                count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ 저장 실패: {entry.title[:10]}... ({e})")
        
        return count

def start_fetch_task():
    fetcher = MKNewsFetcher()

    for cat in fetcher.rss_map.keys():
        added_count = fetcher.run_import(cat)
        print(f"✅ {cat} 카테고리: {added_count}개 기사 추가됨")

    print("🔄 금융 카테고리 수집 시작 (스크래핑 방식)...")
    finance_links = fetcher.fetch_financial_links(limit=5)
    added_finance = fetcher.run_import_from_links('금융', finance_links)
    print(f"✅ 금융 카테고리(Web): {added_finance}개 추가됨")