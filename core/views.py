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
    recommended_articles = Article.objects.none()

    if user.is_authenticated:
        seven_days_ago = now - timedelta(days=7)
        
        # 18개 소분류에 대한 점수를 annotate로 계산
        # (기사를 읽거나 퀴즈를 풀 때 이 18개 소분류에 대한 UserInterest 레코드가 생성됩니다)
        user_interests = UserInterest.objects.filter(user=user).annotate(
            dynamic_weakness=Case(
                When(last_wrong_at__gte=now - timedelta(days=3), then=Value(4)),
                When(last_wrong_at__gte=now - timedelta(days=7), then=Value(2)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            unlearned_bonus=Case(
                When(Q(last_viewed_at__lt=seven_days_ago) | Q(last_viewed_at__isnull=True), then=Value(5)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )

        # 소분류 점수 합산 상위 3개 키워드 추출
        top_weak_cats = user_interests.annotate(
            total_priority=F('dynamic_weakness') + F('unlearned_bonus') + F('weakness_score')
        ).filter(total_priority__gt=0).order_by('-total_priority')[:3]

        if top_weak_cats.exists():
            target_keywords = [tw.interest.name for tw in top_weak_cats]
            
            # 기사의 sub_category_names(18개 중 해당되는 것들) 필터링
            query = Q()
            for kw in target_keywords:
                query |= Q(sub_category_names__contains=kw)
            
            recommended_articles = Article.objects.filter(query).distinct().order_by('-published_at')[:6]

    if not recommended_articles.exists():
        recommended_articles = Article.objects.order_by('-published_at')[:6]

    return render(request, 'main.html', {
        'recommended_articles': recommended_articles,
        'latest_articles': Article.objects.order_by('-published_at')[:10],
    })