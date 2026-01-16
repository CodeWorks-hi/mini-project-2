# 🚗 Hyundai & Kia ERP 차량 관리 시스템

현대·기아 자동차의 해외 판매 데이터를 분석하고, AI 기반 예측 및 추천 시스템을 제공하는 통합 ERP 대시보드입니다.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hyundai-kia-dashboard-codeworks.streamlit.app/)

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 및 실행](#-설치-및-실행)
- [사용 방법](#-사용-방법)
- [데이터 구조](#-데이터-구조)
- [AI 모델](#-ai-모델)
- [주요 모듈](#-주요-모듈)

---

## 🎯 프로젝트 소개

본 프로젝트는 **현대·기아 자동차의 해외 판매 데이터**(2016-2025년)를 활용하여 실시간 판매 현황을 모니터링하고, 머신러닝 기반 예측 및 추천 시스템을 제공하는 통합 ERP 솔루션입니다.

### 핵심 가치
- 📊 **데이터 기반 의사결정**: 실시간 판매 데이터 시각화 및 분석
- 🤖 **AI 예측 시스템**: LSTM/SARIMAX 모델을 통한 판매량 예측
- 💡 **지능형 추천**: 시장 상황에 맞는 차량 및 전략 추천
- 🌐 **글로벌 관점**: 지역별, 공장별, 차종별 다각도 분석

---

## ✨ 주요 기능

### 1. 📈 통합 대시보드
- 실시간 KPI 모니터링 (총 판매량, 전월 대비 증감률, 지역별 성과)
- 인터랙티브 차트 및 그래프 (지역별/차종별/공장별)
- 트렌드 분석 및 인사이트 제공
- 최신 자동차 산업 뉴스 크롤링

### 2. 🏭 생산 관리
- 공장별 생산 현황 모니터링
- 차종별 생산량 추이 분석
- 생산 효율성 지표

### 3. 📦 재고 관리
- 실시간 재고 현황 추적
- 지역별/차종별 재고 분석
- 재고 최적화 인사이트

### 4. 🌍 판매 관리
- 지역별 판매 실적 분석
- 수출/내수 판매 비교
- 차종별 판매 트렌드

### 5. 🔮 AI 예측 시스템
- **LSTM 모델**: 지역별/공장별/차종별 판매량 예측
- **SARIMAX 모델**: 시계열 기반 판매 예측
- 다양한 기간 설정 (1개월, 3개월, 6개월, 12개월)
- 시각화된 예측 결과 제공

### 6. 🧠 AI 분석 시스템
- 판매 데이터 기반 차량 추천
- 시장 트렌드 분석
- 전략적 인사이트 제공

### 7. 📊 데이터 뷰어
- 원본 데이터 탐색 및 필터링
- 데이터 다운로드 (CSV, Excel)
- 커스텀 쿼리 기능

---

## 🛠 기술 스택

### Frontend & Framework
- **Streamlit**: 웹 애플리케이션 프레임워크
- **Plotly**: 인터랙티브 시각화
- **Altair**: 선언적 시각화
- **Matplotlib/Seaborn**: 통계 시각화

### AI/ML
- **TensorFlow 2.18.0**: 딥러닝 프레임워크
- **Keras 3.5.0+**: 고수준 신경망 API
- **PyTorch 2.0.0**: 딥러닝 프레임워크
- **Scikit-learn**: 머신러닝 라이브러리

### Data Processing
- **Pandas 2.1.0+**: 데이터 처리 및 분석
- **NumPy 1.26+**: 수치 계산

### Others
- **BeautifulSoup4**: 웹 크롤링
- **ReportLab**: PDF 리포트 생성
- **OpenPyXL**: Excel 파일 처리

---

## 📁 프로젝트 구조

```
mini-project-2/
│
├── Home.py                      # 메인 진입점 (Streamlit 앱)
├── requirements.txt             # 패키지 의존성
├── README.md                    # 프로젝트 문서
│
├── components/                  # UI 컴포넌트
│   └── navbar.py               # 네비게이션 바
│
├── core/                        # 핵심 기능
│   ├── i18n.py                 # 다국어 지원
│   └── master_auth.py          # 인증 시스템
│
├── modules/                     # 주요 기능 모듈
│   ├── dashboard.py            # 통합 대시보드
│   ├── dashboard_cards.py      # 대시보드 카드 컴포넌트
│   ├── dashboard_charts.py     # 차트 생성
│   ├── dashboard_data_loader.py # 데이터 로더
│   ├── dashboard_filter.py     # 필터 기능
│   ├── dashboard_insight.py    # 인사이트 생성
│   ├── dashboard_kpi.py        # KPI 지표
│   ├── dashboard_news.py       # 뉴스 크롤링
│   ├── production.py           # 생산 관리
│   ├── inventory.py            # 재고 관리
│   ├── export.py               # 판매 관리
│   ├── prediction.py           # AI 예측
│   ├── recommendations.py      # AI 추천
│   ├── analytics.py            # 분석 기능
│   ├── data.py                 # 데이터 뷰어
│   └── intro.py                # 시스템 소개
│
├── data/                        # 데이터 디렉토리
│   ├── raw/                    # 원본 데이터
│   │   ├── 현대/              # 현대 자동차 데이터
│   │   └── 기아/              # 기아 자동차 데이터
│   └── processed/              # 전처리된 데이터
│       ├── hyundai-by-car.csv
│       ├── hyundai-by-plant.csv
│       ├── hyundai-by-region.csv
│       ├── kia-by-car.csv
│       ├── kia-by-plant.csv
│       └── kia-by-region.csv
│
├── extra_data/                  # 추가 경제 지표 데이터
│   ├── processed/
│   │   ├── 경제 성장 관련/
│   │   ├── 금융 환경 관련/
│   │   ├── 소비 심리 관련/
│   │   ├── 실제 판매 관련/
│   │   └── 재고 관련/
│   └── raw/
│
├── models/                      # 학습된 AI 모델
│   ├── lstm_region_*.h5        # 지역별 LSTM 모델
│   ├── lstm_plant_*.h5         # 공장별 LSTM 모델
│   ├── lstm_car_*.h5           # 차종별 LSTM 모델
│   └── sarimax_*.pkl           # SARIMAX 모델
│
├── jupyter_notebooks/           # 개발용 노트북
│   ├── 데이터_전처리/
│   ├── 데이터_분석/
│   ├── 모델_개발/
│   ├── 시각화/
│   └── 클러스터링/
│
├── fonts/                       # 한글 폰트
│   └── NanumGothic*
│
└── images/                      # 이미지 리소스
    ├── favicon.ico
    ├── hyunlogo.png
    └── result/                 # 분석 결과 이미지
```

---

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.8 이상
- pip 패키지 관리자

### 설치 방법

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/mini-project-2.git
cd mini-project-2
```

2. **가상환경 생성 (권장)**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

### 실행 방법

#### 로컬 실행
```bash
streamlit run Home.py
```

브라우저에서 `http://localhost:8501`로 접속

#### 온라인 데모
🌐 [Streamlit Cloud에서 실행](https://hyundai-kia-dashboard-codeworks.streamlit.app/)

**로그인 정보**
- **ID**: `admin`
- **PW**: `admin123`

---

## 📖 사용 방법

### 1. 로그인
- 앱 실행 시 로그인 화면에서 인증 정보 입력

### 2. 대시보드 탐색
- 상단 탭을 통해 원하는 기능 선택
- 필터를 활용한 데이터 조회

### 3. 예측 실행
1. **AI 예측 시스템** 탭 선택
2. 예측 유형 선택 (지역별/공장별/차종별)
3. 대상 선택 및 예측 기간 설정
4. **예측 실행** 버튼 클릭
5. 시각화된 결과 확인

### 4. 데이터 다운로드
- **데이터 뷰어** 탭에서 필터링 후 CSV/Excel 다운로드

---

## 📊 데이터 구조

### 주요 데이터셋

#### 1. 지역별 판매 데이터
```
지역, 년도, 월, 판매량, 판매구분(수출/내수)
```

#### 2. 공장별 생산 데이터
```
공장명, 차종, 년도, 월, 생산량, 판매구분
```

#### 3. 차종별 판매 데이터
```
차종명, 년도, 월, 판매량, 판매구분
```

### 데이터 기간
- **2016년 ~ 2025년** 월별 데이터
- 현대 자동차 및 기아 자동차 데이터 포함

---

## 🤖 AI 모델

### LSTM (Long Short-Term Memory)
- **목적**: 시계열 판매 데이터 예측
- **구조**: 
  - 입력층: 과거 12개월 데이터
  - 은닉층: LSTM 레이어 (50-100 유닛)
  - 출력층: 향후 1-12개월 예측
- **학습 데이터**: 2016-2024년 판매 데이터
- **적용 대상**: 
  - 지역별 모델 (12개 모델)
  - 공장별 모델 (3개 모델)
  - 차종별 모델 (3개 모델)

### SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous factors)
- **목적**: 계절성을 고려한 판매 예측
- **특징**: 
  - 계절적 패턴 자동 감지
  - 외부 변수 통합 가능
- **적용 대상**: 주요 지역 (미국) 판매 예측

### 모델 성능
- **MAPE (Mean Absolute Percentage Error)**: 평균 8-15%
- **R² Score**: 0.75-0.92
- **검증 방식**: Time-series cross-validation

---

## 📦 주요 모듈

### Dashboard Module (`modules/dashboard.py`)
통합 대시보드의 메인 로직을 담당하며, 하위 모듈들을 조합하여 전체 UI를 구성합니다.

### Prediction Module (`modules/prediction.py`)
- 학습된 LSTM/SARIMAX 모델 로드
- 사용자 입력 기반 예측 실행
- 예측 결과 시각화

### Recommendations Module (`modules/recommendations.py`)
- 판매 데이터 분석
- 시장 트렌드 기반 차량 추천
- 전략적 인사이트 생성

### Data Module (`modules/data.py`)
- 데이터 로드 및 필터링
- 데이터 내보내기 (CSV, Excel)
- 데이터 전처리 파이프라인

---

## 🔧 환경 변수

필요한 경우 `.env` 파일 생성:

```env
# Streamlit 설정
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost

# 로그 레벨
LOG_LEVEL=INFO

# 데이터 경로 (선택)
DATA_PATH=./data
MODEL_PATH=./models
```

---

## 🐛 문제 해결

### 일반적인 오류

#### 1. 모듈 import 오류
```bash
pip install --upgrade -r requirements.txt
```

#### 2. TensorFlow/Keras 버전 충돌
```bash
pip uninstall tensorflow keras
pip install tensorflow==2.18.0 keras>=3.5.0
```

#### 3. 한글 폰트 오류
- `fonts/` 디렉토리에 NanumGothic 폰트가 있는지 확인
- matplotlib 폰트 캐시 삭제:
```bash
rm -rf ~/.matplotlib
```

#### 4. 메모리 부족
- 예측 기간을 짧게 설정
- 데이터 필터링 활용

---

## 📝 개발 로드맵

### v1.0 (현재)
- ✅ 통합 대시보드
- ✅ LSTM 기반 예측 시스템
- ✅ 기본 추천 시스템

### v1.1 (예정)
- [ ] 실시간 데이터 연동
- [ ] 사용자 권한 관리 고도화
- [ ] 모바일 최적화

### v2.0 (계획)
- [ ] Transformer 기반 예측 모델
- [ ] 자동 리포트 생성
- [ ] RESTful API 제공
- [ ] 다국어 지원 확대

---

## 👥 기여 방법

프로젝트에 기여하고 싶으신가요? 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 교육 목적으로 개발되었습니다.

---

## 📧 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/yourusername/mini-project-2/issues)

---

## 🙏 감사의 말

- **현대자동차 & 기아자동차**: 데이터 제공
- **Streamlit**: 훌륭한 웹 프레임워크
- **TensorFlow/Keras**: AI 모델 개발 도구

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

Made with ❤️ by ENZO

</div>
