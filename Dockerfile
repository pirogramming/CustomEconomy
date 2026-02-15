# 1. 파이썬 3.10 버전의 베이스 이미지 사용
FROM python:3.10-slim

# 2. 필수 시스템 패키지 설치 (newspaper3k 등 라이브러리 의존성)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 소스 코드 복사
COPY . .

# 6. Django 환경변수 설정
ENV DJANGO_SETTINGS_MODULE=myproject.settings
ENV PYTHONUNBUFFERED=1

# (참고) Airflow 환경에서는 여기서 직접 실행 명령을 내리지 않고 
# docker-compose가 이 이미지를 가져다 씁니다.