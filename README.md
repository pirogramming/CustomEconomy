# 📊 커스텀 경제 (Custom Economy)

> 🧠 **경제 뉴스를 ‘내 수준과 내 삶의 관점’으로 다시 설명해주는 AI 기반 개인화 경제 학습 플랫폼**

커스텀 경제는  
어려운 경제 기사를 **AI가 쉬운 언어로 재풀이**하고,  
**퀴즈 · 학습 기록 · 추천 · 리그 시스템**을 통해  
사용자가 자연스럽게 경제 문해력을 키울 수 있도록 돕는 웹 서비스입니다.

---

## 🚀 프로젝트 배경

많은 사람들이 경제 뉴스를 읽어도

- 용어가 어렵고
- 맥락이 이해되지 않고
- 내 삶과 어떤 관련이 있는지 모르기 때문에

👉 결국 읽기를 포기합니다.

우리는  
**"경제를 공부하는 게 아니라, 이해하게 만들자"**  
라는 목표로 이 서비스를 만들었습니다.

---

## ✨ 핵심 기능

### 📰 기사 학습
- 카테고리별 경제 뉴스 제공 (경제/금융/기업/부동산/증권)
- 기사 요약 및 핵심 내용 표시

### 🤖 AI 재풀이 (핵심 기능)
- 난이도 선택: EASY / MID / PRO
- 상황(모드) 선택: 소비 / 투자 / 물가 / 대출 / 고용 등
- 기사 내용을 **내 수준에 맞게 설명**
- 핵심 경제 용어 자동 추출 + 정의 제공

### 🧩 퀴즈 시스템
- 기사 기반 자동 퀴즈 생성
- 객관식 / 용어 정의 문제
- 즉시 채점 + 해설 제공

### 🎯 개인화 추천
- 학습 기록 분석
- 관심 분야 & 약점 기반 기사 추천
- 메인 화면 맞춤 피드 제공

### 🏆 리그 (게이미피케이션)
- XP 적립
- 출석 체크
- 5단계 리그 시스템
- 사용자 랭킹 경쟁

### 📘 마이페이지
- 틀린 문제 복습
- 학습한 경제 용어 정리
- 스크랩 기사 모아보기
- 프로필 관리

---

## 🧠 서비스 구조

```
CustomEconomy
├─ accounts
│  ├─ adapters.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ static
│  │  ├─ league.css
│  │  ├─ login.css
│  │  ├─ mypage.css
│  │  └─ signup.css
│  ├─ templates
│  │  ├─ league.html
│  │  ├─ login.html
│  │  ├─ mypage.html
│  │  └─ signup.html
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ articles
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ static
│  │  ├─ articleList.css
│  │  └─ articleList.js
│  ├─ tasks.py
│  ├─ templates
│  │  └─ articleList.html
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ config
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ __init__.py
├─ core
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ static
│  │  ├─ base.css
│  │  ├─ img
│  │  │  └─ fox-avatar.png
│  │  └─ main.css
│  ├─ templates
│  │  ├─ base.html
│  │  └─ main.html
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ explanations
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ static
│  │  └─ ai_explain.css
│  ├─ templates
│  │  └─ ai_explain.html
│  ├─ tests.py
│  ├─ urls.py
│  ├─ utils.py
│  ├─ views.py
│  └─ __init__.py
├─ manage.py
├─ quizzes
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ services.py
│  ├─ static
│  │  ├─ quiz.css
│  │  └─ quiz.js
│  ├─ templates
│  │  ├─ quiz.html
│  │  ├─ quiz_result.html
│  │  ├─ session_result.html
│  │  └─ wrong_note.html
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ b_build_term.py
│  ├─ c_build_quiz.py
│  ├─ data
│  │  ├─ concept_bank.json
│  │  ├─ master_dictionary.json
│  │  └─ term_800.pdf
│  └─ load_to_db.py
├─ static
│  └─ css
│     ├─ auth.css
│     ├─ base.css
│     ├─ detail.css
│     ├─ explore.css
│     ├─ league.css
│     ├─ learning.css
│     ├─ main.css
│     └─ mypage.css
├─ templates
│  ├─ base.html
│  ├─ detail.html
│  ├─ explore.html
│  ├─ league.html
│  ├─ login.html
│  ├─ main.html
│  ├─ mypage.html
│  ├─ signup.html
│  └─ summary.html
└─ terms
   ├─ admin.py
   ├─ apps.py
   ├─ migrations
   │  ├─ 0001_initial.py
   │  └─ __init__.py
   ├─ models.py
   ├─ static
   │  └─ terms.css
   ├─ templates
   │  └─ terms.html
   ├─ tests.py
   ├─ urls.py
   ├─ views.py
   └─ __init__.py

```