from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Airflow 환경에서 Django 모델을 불러오기 위한 경로 설정
sys.path.append('/app')

def get_fetcher():
    from articles.tasks import run_popular_news, run_category_news, run_financial_news
    return run_popular_news, run_category_news, run_financial_news

default_args = {
    'owner': 'sihyun',
    'start_date': datetime(2026, 2, 14),
    'retries': 0, # 실패 시 재시도 안 함 (시현님 요청)
}

with DAG(
    dag_id='mk_news_collector_v1',
    default_args=default_args,
    schedule='0 0/3 * * *', # 3시간마다
    catchup=False,
    tags=['news', 'django'],
) as dag:

    # 1. 인기 뉴스 (선행 작업)
    def task_popular():
        _, _, _ = get_fetcher() # import용
        from articles.tasks import run_popular_news
        run_popular_news()

    popular_task = PythonOperator(
        task_id='step_popular_news',
        python_callable=task_popular
    )

    # 2. 카테고리별 병렬 수집
    categories = ['경제', '기업', '증권', '부동산']
    
    for cat in categories:
        def task_cat(c=cat):
            from articles.tasks import run_category_news
            run_category_news(c)

        cat_task = PythonOperator(
            task_id=f'step_category_{cat}',
            python_callable=task_cat,
            trigger_rule='all_done' # 이전 작업 실패해도 무조건 실행
        )
        
        popular_task >> cat_task # 인기뉴스 완료 후 각 카테고리들 병렬 시작

    # 3. 금융 뉴스 (별도 링크 수집)
    def task_financial():
        from articles.tasks import run_financial_news
        run_financial_news()

    financial_task = PythonOperator(
        task_id='step_financial_news',
        python_callable=task_financial,
        trigger_rule='all_done'
    )

    popular_task >> financial_task