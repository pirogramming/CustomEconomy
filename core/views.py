from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Case, When, Value, IntegerField, F
from articles.models import Article
from accounts.models import UserInterest

# Create your views here.

def main_view(request):
    user = request.user
    now = timezone.now()

    
    # 1. 초기화 (데이터가 없을 경우를 대비)
    interest_articles = Article.objects.none()
    weak_articles = Article.objects.none()
    user_sub_interests = UserInterest.objects.none()
    has_learning_history = False # 학습 이력 여부 판단 플래그

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
        top_interests = user_sub_interests.order_by('-interest_score')[:3]
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
                # 최종 계산: DB점수 + 최근오답가중치 + 미학습보너스
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