# GitHub 원본 UI 비교 및 React 전환 메모

## 가져온 원본 파일

원격 저장소 `https://github.com/pyoseonchoi/COSS_Hackerton`의 기존 정적 UI 파일을 현재 작업물과 섞지 않고 아래 경로에 복사했다.

```text
reference/original-static/
├── index.html
├── app.js
└── style.css
```

이 파일들은 비교용 원본이며, 현재 실행되는 화면은 `frontend/`의 React 앱이다.

## 현재 React 앱

```text
frontend/src/
├── App.jsx
├── components/
├── data/
├── utils/
├── main.jsx
└── styles.css
```

현재 React 앱은 귀농 후 현재 세후소득을 대체하려면 필요한 재배 규모, 초기 투자비, 투자 회수 기간을 계산하는 화면이다.

## 원본 정적 UI 구성

원본 `index.html`은 아래 4개 섹션으로 구성되어 있다.

| 섹션 ID | 원본 화면 | React 전환 방향 |
| --- | --- | --- |
| `overview` | 개인 맞춤형 입지 선호도 설정 | `PreferencePanel` 컴포넌트로 분리 |
| `public-data` | 1차 농지 후보지 탐색 | `CandidateExplorer` 컴포넌트로 분리 |
| `drone-analysis` | 2차 미시 드론 영상 분석 | `DroneAnalysis` 컴포넌트로 분리 |
| `final-recommendation` | 최종 창농 적합도 및 정책 가이드 | `FinalRecommendation` 컴포넌트로 분리 |

## 원본 JavaScript 기능

원본 `app.js`의 주요 함수는 다음과 같다.

| 원본 함수 | 역할 | React 전환 방식 |
| --- | --- | --- |
| `setupEventListeners` | DOM 이벤트 직접 연결 | JSX 이벤트 핸들러로 대체 |
| `setupPreferenceSliders` | 선호도 슬라이더 값 표시 | `useState`로 값 관리 |
| `switchSection` | 사이드바 섹션 전환 | `activeSection` 상태로 전환 |
| `fetchCandidates` | 후보지 API 조회 | `useEffect` + `fetch`로 전환 |
| `fetchCandidatesWithPreferences` | 선호도 기반 후보지 조회 | 입력 상태를 API query/form으로 전달 |
| `populateCandidatesTable` | 후보지 테이블 DOM 삽입 | 후보지 배열을 JSX map으로 렌더링 |
| `populateCandidateSelect` | 후보지 select DOM 삽입 | 후보지 배열을 JSX option으로 렌더링 |
| `initLeafletMap` | Leaflet 지도 초기화 | `MapPanel` 컴포넌트에서 `useEffect`로 초기화 |
| `updateRadarChart` | 후보지 레이더 차트 갱신 | Chart 컴포넌트 props 변경으로 갱신 |
| `runDroneAnalysis` | 이미지 업로드 분석 API 호출 | `DroneAnalysis`에서 FormData submit |
| `updateDroneBarChart` | 드론 지표 차트 갱신 | 분석 결과 state 기반 차트 렌더링 |
| `setupFinalRecommendation` | 최종 추천 UI 갱신 | `FinalRecommendation` props/state 기반 렌더링 |
| `initWeightPieChart` | 가중치 파이 차트 초기화 | 고정 chart data를 컴포넌트화 |
| `downloadJsonReport` | JSON 다운로드 | React 버튼 핸들러로 유지 |
| `showLoader` / `hideLoader` | 로딩 오버레이 표시 | `isLoading` 상태로 대체 |

## React로 가져올 우선순위

1. 현재 소득 계산기 유지
   - 지금 만든 `App.jsx`의 소득 대체 계산 플로우는 유지한다.
   - 이 기능은 원본에 없던 새 랜딩 핵심 기능이다.

2. 원본의 개인 선호도 화면 추가
   - 지역 추천 정확도를 높이는 입력값으로 사용할 수 있다.
   - `PreferencePanel`로 만들고 현재 계산 입력 패널 아래에 배치한다.

3. 원본의 후보지 탐색 화면 React화
   - `CandidateExplorer`로 만들고 `/api/candidates` 데이터를 사용한다.
   - 지도는 초기에 생략하거나 Leaflet 컴포넌트로 별도 추가한다.

4. 원본의 드론 분석 화면 React화
   - OpenCV 의존성 설치 문제가 있으므로 UI는 분리하되 API 실패 상태를 명확히 보여준다.
   - 이미지 업로드, 샘플 사용, 분석 결과 카드만 먼저 React화한다.

5. 최종 추천 화면 통합
   - 현재 소득 계산 결과와 원본 입지 진단 결과를 하나의 최종 추천 카드로 합친다.

## 추천 React 컴포넌트 구조

```text
frontend/src/
├── App.jsx
├── components/
│   ├── IncomeCalculator.jsx
│   ├── PreferencePanel.jsx
│   ├── CandidateExplorer.jsx
│   ├── DroneAnalysis.jsx
│   ├── FinalRecommendation.jsx
│   ├── Metric.jsx
│   └── RecommendationCard.jsx
├── data/
│   └── agricultureData.js
├── services/
│   └── api.js
└── utils/
    ├── calculations.js
    └── formatters.js
```

## 주의할 점

- 원본은 DOM 직접 조작 방식이고, React에서는 DOM 삽입 대신 상태와 props로 렌더링해야 한다.
- 원본 `FontAwesome` 아이콘은 현재 React 앱 기준으로 `lucide-react` 아이콘으로 교체한다.
- 원본 지도/차트 라이브러리는 바로 섞지 말고, 필요한 경우 컴포넌트 단위로 도입한다.
- 현재 Windows ARM64 환경에서는 `opencv-python`, `pyarrow` 설치가 실패했으므로 드론 분석 API는 선택 기능으로 유지한다.
- 백엔드 루트 `/`와 `/app`는 현재 React 빌드 결과를 서빙한다.
