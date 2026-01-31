import feedparser
import time
import re
from datetime import datetime
from dateutil import parser
from newspaper import Article as NewsArticle
from .models import Article, Category

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