# 귀농 소득 대체 계산기

현재 월 세후 실수령액을 기준으로, 귀농 후 비슷한 수준의 소득을 만들기 위해 필요한 재배 규모와 초기 투자비를 계산하는 React 기반 MVP입니다.

## 구조

```text
COSS_Hackerton/
├── frontend/                 # React/Vite 프론트엔드 소스
│   └── src/
│       ├── App.jsx
│       ├── components/       # 화면 컴포넌트
│       ├── data/             # 지역/작물 목데이터
│       ├── utils/            # 계산식과 포맷터
│       └── styles.css
├── static/react-app/         # React 빌드 결과
├── main.py                   # FastAPI 서버 및 React 정적 서빙
├── src/                      # 기존 분석 API 보조 모듈
├── data/                     # 백엔드 목데이터
└── requirements.txt          # FastAPI 실행 최소 의존성
```

## 실행

### 1. 프론트엔드 개발 서버

```bash
npm install
npm run dev
```

Vite 개발 서버가 기본적으로 `http://localhost:5173`에서 실행됩니다.

### 2. 프로덕션 빌드

```bash
npm run build
```

빌드 결과는 `static/react-app/`에 생성되며 FastAPI가 이 파일을 서빙합니다.

### 3. 백엔드 서버

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

실행 후 `http://127.0.0.1:8000/`로 접속하면 React 앱이 표시됩니다.

## 계산 기준

- 소득 비교는 세전 연봉이 아니라 월 세후 실수령액 기준입니다.
- 지역별 농지 가격, 임대료, 기후 키워드는 현재 프론트엔드 목데이터입니다.
- 작물별 수익성, 시설비, 장비비, 노동 강도도 MVP용 추정값입니다.
- 결과는 수익 보장이 아니라 귀농으로 현재 소득을 대체하기 위한 규모와 초기 비용의 참고 추정치입니다.

## 주요 기능

- 현재 월 세후 실수령액과 생활비 입력
- 초기 투자 가능 금액 입력
- 희망 지역, 농지 확보 방식, 노동 강도, 농업 유형 선택
- 목표 연 세후소득 계산
- 작물별 필요 재배면적과 초기 투자비 계산
- 안정형, 균형형, 수익형 추천안 비교

## 참고

드론 이미지 분석 API 관련 코드는 남겨두었지만, React 소득 계산기 실행에는 필요하지 않습니다. OpenCV 기반 분석 기능을 다시 사용할 경우 별도 환경에서 `numpy`, `opencv-python`, `pillow`, `pyyaml` 등을 설치해 확인해야 합니다.
