FROM python:3.10-slim

# 1. 필수 시스템 패키지 설치 (루트 권한)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 비관리자 권한 사용자 생성 및 폴더 준비 (루트 권한일 때 한 번에 수행)
# 사용자가 없을 때만 생성하고, 필요한 폴더 권한을 미리 설정합니다.
RUN id -u sihyun >/dev/null 2>&1 || useradd -m sihyun && \
    mkdir -p /app/staticfiles && \
    chown -R sihyun:sihyun /app

# 3. 의존성 설치 (캐시 최적화를 위해 소스 복사 전에 수행)
COPY requirements.txt .
# 의존성 설치는 루트 권한으로 하는 것이 시스템 패키지 관리에 안정적입니다.
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# 4. 소스 코드 복사 및 소유권 변경
COPY --chown=sihyun:sihyun . .

# 5. 사용자 전환 (보안 정석)
# 이제부터 실행되는 모든 명령(gunicorn 등)은 sihyun 권한으로 돌아갑니다.
USER sihyun

ENV PYTHONUNBUFFERED=1