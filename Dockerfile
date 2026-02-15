FROM python:3.10-slim

# 1. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Gunicorn 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

COPY . .

# 3. 비관리자 권한 사용자 생성 (보안 정석)
RUN useradd -m sihyun
RUN chown -R sihyun:sihyun /app
USER sihyun

ENV PYTHONUNBUFFERED=1