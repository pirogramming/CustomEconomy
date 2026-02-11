from django.shortcuts import render
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from django.db.models import Q, Case, When, Value, IntegerField, F
from articles.models import Article
from accounts.models import UserInterest
import os
import requests
import yfinance as yf

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 한국은행 API 연동 함수들
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_bok_data(api_key, stat_code, item_code, days_back=7):
    """
    한국은행 ECOS API에서 데이터 조회
    """
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        # API URL 구성
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/{stat_code}/D/{start_str}/{end_str}/{item_code}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        
        # 응답 파싱
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            rows = data['StatisticSearch']['row']
            if rows and len(rows) > 0:
                print(f"✅ 데이터 발견: {rows[-1]}")
                return rows[-1]
        
        print(f"⚠️ StatisticSearch.row가 없거나 비어있음")
        return None
        
    except Exception as e:
        print(f"❌ BOK API 요청 실패 ({item_code}): {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_kospi_index():
    """KOSPI 지수 조회"""
    cache_key = 'bok_kospi'
    cached = cache.get(cache_key)
    if cached:
        print(f"✅ KOSPI 캐시 사용: {cached}")
        return cached
    
    api_key = os.getenv('BOK_API_KEY')
    if not api_key:
        print("⚠️ BOK_API_KEY가 없습니다")
        return {'value': 2500.0, 'label': 'KOSPI', 'unit': ''}
    
    # 🔍 디버깅용 로그 추가
    print(f"🔍 KOSPI API 호출 중... (통계표: 802Y001, 항목: 0001000)")
    data = fetch_bok_data(api_key, '802Y001', '0001000')
    
    if data:
        print(f"✅ KOSPI API 응답: {data}")
        result = {
            'value': float(data.get('DATA_VALUE', 0)),
            'label': 'KOSPI',
            'unit': ''
        }
        cache.set(cache_key, result, 3600)
        return result
    else:
        print("❌ KOSPI API 응답 없음 - 기본값 사용")
    
    return {'value': 2500.0, 'label': 'KOSPI', 'unit': ''}


def get_exchange_rate():
    """
    원/달러 환율 조회 (yfinance 사용 - 실시간)
    KRW=X: 원/달러 환율 ticker
    """
    cache_key = 'yf_exchange'
    cached = cache.get(cache_key)
    if cached:
        print(f"✅ 환율 캐시 사용: {cached}")
        return cached
    
    try:
        # 🆕 yfinance로 원/달러 환율 조회
        print("🔍 yfinance로 환율 조회 중... (Ticker: KRW=X)")
        
        krw_usd = yf.Ticker("KRW=X")
        
        # 최신 데이터 가져오기 (1분 단위)
        hist = krw_usd.history(period="1d", interval="1m")
        
        if not hist.empty:
            # 가장 최근 종가 사용
            latest_rate = hist['Close'].iloc[-1]
            
            result = {
                'value': round(float(latest_rate), 2),
                'label': '환율',
                'unit': '원/USD'
            }
            
            print(f"✅ yfinance 환율 조회 성공: {result}")
            
            # 1분 캐싱 (실시간성 유지)
            cache.set(cache_key, result, 60)
            return result
        else:
            print("⚠️ yfinance에서 데이터를 가져오지 못함")
            
    except Exception as e:
        print(f"❌ yfinance 환율 조회 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # 실패 시 기본값 반환
    return {'value': 1320.5, 'label': '환율', 'unit': '원/USD'}

def get_base_rate():
    """기준금리 조회 (월별 데이터)"""
    cache_key = 'bok_interest'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    api_key = os.getenv('BOK_API_KEY')
    if not api_key:
        return {'value': 3.25, 'label': '기준금리', 'unit': '%'}
    
    try:
        # 기준금리는 월별 데이터이므로 다르게 처리
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 3개월 전
        start_str = start_date.strftime('%Y%m')
        end_str = end_date.strftime('%Y%m')
        
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/722Y001/M/{start_str}/{end_str}/0101000"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            rows = data['StatisticSearch']['row']
            if rows and len(rows) > 0:
                latest = rows[-1]
                result = {
                    'value': float(latest.get('DATA_VALUE', 0)),
                    'label': '기준금리',
                    'unit': '%'
                }
                cache.set(cache_key, result, 21600)  # 6시간 캐시 (금리는 자주 안 바뀜)
                return result
    except Exception as e:
        print(f"❌ 기준금리 조회 실패: {e}")
    
    return {'value': 3.25, 'label': '기준금리', 'unit': '%'}


def get_economic_indicators():
    """모든 경제 지표 조회"""
    return {
        'kospi': get_kospi_index(),
        'exchange': get_exchange_rate(),
        'interest': get_base_rate()
    }

def main_view(request):
    user = request.user
    now = timezone.now()

    # 1. 초기화 (데이터가 없을 경우를 대비)
    interest_articles = Article.objects.none()
    weak_articles = Article.objects.none()
    user_sub_interests = UserInterest.objects.none()
    has_learning_history = False

    # 상단 인기 뉴스
    latest_articles = Article.objects.filter(is_popular=True).order_by('-published_at')[:1]
    if not latest_articles.exists():
        latest_articles = Article.objects.order_by('-published_at')[:1]
        
    if user.is_authenticated:
        # --- [1단계] 점수 및 가중치 계산 시간 설정 ---
        seven_days_ago = now - timedelta(days=7)
        three_days_ago = now - timedelta(days=3)

        # 소분류(SUB)만 필터링해서 가져오기
        user_sub_interests = UserInterest.objects.filter(
            user=user, 
            interest__category_type='SUB'
        ).select_related('interest')

        # 학습 이력 체크 (기사 조회나 퀴즈 참여 여부)
        has_learning_history = user_sub_interests.filter(
            Q(interest_score__gt=0) | Q(weakness_score__gt=0) | Q(last_viewed_at__isnull=False)
        ).exists()

        # --- [2단계] 맞춤형 관심 뉴스 추출 ---
        top_interests = user_sub_interests.annotate(
            # 실시간 가중치 계산: 7일 내 조회(+5)
            recency_weight=Case(
                When(last_viewed_at__gte=seven_days_ago, then=Value(5)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).annotate(
            # 최종 점수 = 기존 관심 점수 + 최근 학습 가중치
            final_interest_score=F('interest_score') + F('recency_weight')
        ).order_by('-final_interest_score')[:3]
        
        if top_interests.exists():
            interest_q = Q()
            for ui in top_interests:
                interest_q |= Q(sub_interests__name=ui.interest.name)
            interest_articles = Article.objects.filter(interest_q).distinct().order_by('?')[:3]

        # --- [3단계] 맞춤형 취약 뉴스 추출 ---
        if has_learning_history:
            weak_top_interests = user_sub_interests.annotate(
                # 실시간 가중치 계산: 3일 내 오답(+4), 7일 내 오답(+2)
                quiz_weight=Case(
                    When(last_wrong_at__gte=three_days_ago, then=Value(4)),
                    When(last_wrong_at__gte=seven_days_ago, then=Value(2)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                # 미학습 보너스: 7일간 안 봤으면 +5
                unlearned_bonus=Case(
                    When(last_viewed_at__lt=seven_days_ago, then=Value(5)),
                    When(last_viewed_at__isnull=True, then=Value(5)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).annotate(
                # 최종 점수 = DB점수 + 최근 오답 가중치 + 미학습 보너스
                final_weak_score=F('weakness_score') + F('quiz_weight') + F('unlearned_bonus')
            ).order_by('-final_weak_score')[:3]

            if weak_top_interests.exists():
                weak_q = Q()
                for ui in weak_top_interests:
                    weak_q |= Q(sub_interests__name__icontains=ui.interest.name)
                
                # 관심 뉴스와 겹치지 않게 제외하고 추출
                interest_ids = [a.id for a in interest_articles] if hasattr(interest_articles, '__iter__') else interest_articles.values_list('id', flat=True)
                weak_articles = Article.objects.filter(weak_q).exclude(id__in=interest_ids).distinct().order_by('?')[:3]

    # --- [4단계] 데이터 부족 시 보완 ---
    # 1. 관심 뉴스 부족(또는 신규/비로그인) 시 인기 뉴스로 채움
    if interest_articles.count() < 3:
        needed = 3 - interest_articles.count()
        already_picked = [a.id for a in interest_articles]
        extra = Article.objects.filter(is_popular=True).exclude(id__in=already_picked).order_by('?')[:needed]
        interest_articles = list(interest_articles) + list(extra)

    # 2. 약점 뉴스 부족 시 랜덤 뉴스로 채움 (단, 로그인 유저이면서 학습 이력이 있을 때만)
    if has_learning_history and len(weak_articles) < 3:
        needed = 3 - len(weak_articles)
        already_picked = [a.id for a in interest_articles] + [a.id for a in weak_articles]
        extra_weak = Article.objects.exclude(id__in=already_picked).order_by('?')[:needed]
        weak_articles = list(weak_articles) + list(extra_weak)

    return render(request, 'main.html', {
        'interest_articles': interest_articles,
        'weak_articles': weak_articles,
        'latest_articles': latest_articles,
        'user_has_interests': user_sub_interests.filter(interest_score__gt=0).exists(),
        'has_learning_history': has_learning_history,
    })
    
def economic_indicators(request):
    """
    모든 페이지에서 사용할 수 있는 경제 지표 Context Processor
    """
    return {
        'kospi': get_kospi_index(),
        'exchange_rate': get_exchange_rate(),
        'interest_rate': get_base_rate(),
    }