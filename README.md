# 📊 커스텀 경제 (Custom Economy)

개발 기간 : 2026.01.20 - 2026.02.19

> **경제 뉴스를 ‘내 수준과 내 삶의 관점’으로 다시 설명해주는 AI 기반 개인화 경제 학습 플랫폼**

어려운 경제 기사를 **AI가 쉬운 언어로 재풀이**하고, **퀴즈 · 학습 기록 · 추천 · 리그 시스템**을 통해 사용자가 자연스럽게 경제 문해력을 키울 수 있도록 돕는 웹 서비스입니다.

"경제를 공부하는 게 아니라, 이해하게 만들자"라는 목표로 시작되었습니다.

### Custom Economy url : [https://customeconomy.duckdns.org](https://www.google.com/search?q=https://customeconomy.duckdns.org)

# 📌 목차

* [❓ 왜 커스텀 경제인가?](https://www.google.com/search?q=%23-%EC%99%9C-%EC%BB%A4%EC%8A%A4%ED%85%80-%EA%B2%BD%EC%A0%9C%EC%9D%B8%EA%B0%80)
* [🎯 주요 기능](https://www.google.com/search?q=%23-%EC%A3%BC%EC%9A%94-%EA%B8%B0%EB%8A%A5)
* [🏗 프로젝트 구조](https://www.google.com/search?q=%23-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EA%B5%AC%EC%A1%B0)
* [🛠 기술 스택](https://www.google.com/search?q=%23-%EA%B8%B0%EC%88%A0-%EC%8A%A4%ED%83%9D)
* [🎯 대상 이용자](https://www.google.com/search?q=%23-%EB%8C%80%EC%83%81-%EC%9D%B4%EC%9A%A9%EC%9E%90)
* [💪🏻 팀원 구성](https://www.google.com/search?q=%23-%ED%8C%80%EC%9B%90-%EA%B5%AC%EC%84%B1)

# ❓ 왜 커스텀 경제인가?

많은 사람들이 경제 뉴스를 읽으려 시도하지만, 용어가 어렵고 맥락이 이해되지 않아 결국 읽기를 포기합니다. 커스텀 경제는 이 문제를 AI와 게이미피케이션으로 해결합니다.

<div align="center">

| 문제 | 설명 |
| --- | --- |
| 🧱 **높은 진입장벽** | 어려운 경제 용어와 복잡한 배경지식 요구 |
| 🧩 **맥락 파악의 어려움** | 거시적인 경제 흐름이 내 삶과 어떤 관련이 있는지 연결하지 못함 |
| 📉 **학습 동기 부족** | 지루한 텍스트 위주의 정보 전달로 인한 흥미 저하 |
| 💨 **휘발성 지식** | 기사를 읽고 넘어가기만 해서 지식이 장기 기억으로 남지 않음 |

</div>

# 🎯 주요 기능

### 1️⃣ AI 맞춤형 기사 재풀이 (Core)

* 난이도 선택: `EASY` / `MID` / `PRO` 수준별 텍스트 변환
* 모드 선택: 내 삶의 관점(소비, 투자, 물가, 대출, 고용 등)에 맞춘 스토리텔링
* 핵심 경제 용어 자동 추출 및 문맥 맞춤형 정의 제공

### 2️⃣ 기사 탐색 및 요약

* 5대 카테고리(경제/금융/기업/부동산/증권)별 주요 뉴스 제공
* 긴 기사를 한눈에 파악할 수 있는 요약 및 핵심 내용 하이라이트

### 3️⃣ 자동 생성 퀴즈 시스템

* 읽은 기사를 바탕으로 AI가 객관식 및 용어 정의 문제 생성
* 즉시 채점과 친절한 해설 제공으로 복습 유도

### 4️⃣ 게이미피케이션 & 리그 시스템

* 기사 읽기, 퀴즈 풀이, 출석 체크를 통한 `XP(경험치)` 적립
* 5단계 리그 시스템을 통한 사용자 간 랭킹 경쟁
* 성취감을 자극하여 지속적인 학습 동기 부여

### 5️⃣ 개인화 학습 관리 (마이페이지)

* 사용자 학습 기록 분석 및 관심/약점 기반 맞춤 기사 추천
* 틀린 퀴즈 복습 노트 및 나만의 경제 용어장 구축
* 스크랩 기사 및 프로필 통합 관리

# 🏗 프로젝트 구조

```
CustomEconomy/
├── accounts/          # 회원 관리, 마이페이지, 프로필
├── articles/          # 경제 뉴스 크롤링/제공, 기사 요약
├── config/            # Django 최상위 설정 및 라우팅
├── core/              # 공통 로직, 베이스 템플릿, 메인 페이지
├── explanations/      # AI 재풀이 엔진 (난이도/상황별 변환)
├── quizzes/           # 퀴즈 자동 생성, 채점, 오답 노트
├── terms/             # 경제 용어 사전, 용어 추출
└── static/            # 정적 파일 (CSS, JS, 이미지)

```

### 📦 앱 상세

<div align="center">

| 앱 | 기능 |
| --- | --- |
| **accounts** | 회원가입/로그인, 마이페이지 데이터, 리그 및 XP 관리, 스크랩 기능 |
| **articles** | 기사 목록 제공, 카테고리 분류, 기사 원문 및 요약본 서빙 |
| **core** | 서비스 메인 랜딩 페이지, 공통 UI/UX 요소 관리 |
| **explanations** | 프롬프트 엔지니어링 기반 AI 난이도/모드 맞춤형 기사 변환 |
| **quizzes** | 기사 본문 기반 퀴즈 생성, 세션별 퀴즈 결과 및 해설, 오답 관리 |
| **terms** | 마스터 경제 용어 딕셔너리 관리, 기사 내 주요 용어 매핑 |

</div>

### 📄 주요 페이지

<div align="center">

| 페이지 | 설명 |
| --- | --- |
| **메인 페이지** | 맞춤형 기사 피드, 오늘의 추천 기사 |
| **탐색 페이지** | 카테고리별 전체 기사 목록 및 검색 |
| **기사 상세 & AI 재풀이** | 원문/요약 보기, 난이도 및 모드 조절, 용어 뜻풀이 툴팁 |
| **퀴즈 & 결과 페이지** | 기사 학습 후 퀴즈 풀이, 즉각적인 채점 및 피드백 |
| **리그 페이지** | 전체 랭킹, 내 등급, XP 획득 내역 |
| **마이페이지** | 개인 프로필, 오답 노트, 스크랩 용어, 스크랩 기사 |

</div>

# 🛠 기술 스택

### Stacks
<div align="center">
  
| 구분 | Stack  |
| :------: |  :------: |
| **FE** | ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) |
| **BE** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) |
| **SERVER** | ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white) |

</div>

<br>

### Tools
<div align="center">
  
![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?style=for-the-badge&logo=figma&logoColor=white) ![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)
</div>

### Collaboration
<div align="center">

![Notion](https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white) ![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

</div>

<br>

# 🎯 대상 이용자

<div align="center">

| 대상 | 설명 |
| --- | --- |
| 🌱 **경제 입문자 (경린이)** | 경제를 처음 공부하려 하지만 어려운 용어와 배경지식에 막막함을 느끼는 분 |
| 🏢 **취준생 & 직장인** | 커리어에 필요한 핵심 시사 상식을 빠르게 채우고 싶은 분 |
| 🧩 **바쁜 현대인** | 자투리 시간을 활용해 빠르고 핵심만 담은 경제 뉴스를 소비하고 싶은 분 |

</div>

# 💪🏻 팀원 구성

<div align="center">

| **양현서** | **강승구** | **공하은** | **안시현** | **장준학** |
| :---: | :---: | :---: | :---: | :---: |
| [<img width="150" height="200" alt="image" src="https://github.com/user-attachments/assets/b3505d51-2868-4646-b5bc-8c8b6d5e3180" /> <br/> @lilyyang0077](https://github.com/lilyyang0077) |  [<img width="150" height="200" alt="image" src="https://github.com/user-attachments/assets/b23fbedd-0b96-476d-9f47-10cd9ec645b1" /> <br/> @SeungKu-Kang](https://github.com/SeungKu-Kang) | [<img width="150" height="200" alt="image" src="https://github.com/user-attachments/assets/285e6fc5-272f-43f2-9397-be9f6a0ad740" /> <br/> @haeuniea](https://github.com/haeuniea) | [<img width="150" height="200" alt="image" src="https://github.com/user-attachments/assets/413e3e80-1f48-4d88-9ff3-a9aa1174a0c7" /> <br/> @xihxxn](https://github.com/xihxxn) | [<img width="150" height="200" alt="image" src="https://github.com/user-attachments/assets/80e2bf69-a8fd-4224-9469-89c2dc746e02" /> <br/> @Greendeer07](https://github.com/Greendeer07) |
| PM / FE | BE | BE | BE | FE |

</div>

<div align="center">

**© 2026 Custom Economy. All rights reserved.**

</div>
