from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import django

# 1. Airflow 환경에서 Django 프로젝트를 찾을 수 있도록 경로 설정
sys.path.append('/app')

def setup_django():
    """Airflow Task 내부에서 Django 모델에 접근하기 위한 초기화 함수"""
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

# ❌ 여기서 get_fetcher 같은 전역 임포트 함수는 지우거나 안 쓰는 게 좋습니다.

default_args = {
    'owner': 'sihyun',
    'start_date': datetime(2026, 2, 14),
    'retries': 0,
}

with DAG(
    dag_id='mk_news_collector_v1',
    default_args=default_args,
    schedule='0 */3 * * *',
    catchup=False,
    tags=['news', 'django'],
) as dag:

    # 1. 인기 뉴스
    def task_popular():
        setup_django()
        # ✅ 함수 내부에서 임포트!
        from articles.tasks import run_popular_news
        print("인기 뉴스 수집 시작...")
        run_popular_news()

    popular_task = PythonOperator(
        task_id='step_popular_news',
        python_callable=task_popular
    )

    # 2. 카테고리별 병렬 수집
    categories = ['경제', '기업', '증권', '부동산']
    
    for cat in categories:
        # c=cat으로 인자를 고정해주는 방식은 아주 좋습니다.
        def task_cat(c=cat):
            setup_django()
            # ✅ 함수 내부에서 임포트!
            from articles.tasks import run_category_news
            print(f"카테고리 뉴스 수집 시작: {c}")
            run_category_news(c)

        cat_task = PythonOperator(
            task_id=f'step_category_{cat}',
            python_callable=task_cat,
            trigger_rule='all_done'
        )
        
        popular_task >> cat_task

    # 3. 금융 뉴스
    def task_financial():
        setup_django()
        # ✅ 함수 내부에서 임포트!
        from articles.tasks import run_financial_news
        print("금융 뉴스 수집 시작...")
        run_financial_news()

    financial_task = PythonOperator(
        task_id='step_financial_news',
        python_callable=task_financial,
        trigger_rule='all_done'
    )

    popular_task >> financial_task