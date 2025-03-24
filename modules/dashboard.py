import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import re

############################
# 1) CSV 파일 로드 함수
############################
@st.cache_data
def load_csv(file_path):
    """CSV 파일을 로드하고, 오류 발생 시 None을 반환합니다."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"파일 로드 오류 ({file_path}): {e}")
        return None

############################
# 2) HTML 태그 제거 함수
############################
def remove_html_tags(text: str) -> str:
    """네이버 뉴스 검색 결과에 포함된 <b> 등 HTML 태그를 제거하기 위한 함수."""
    return re.sub(r"<.*?>", "", text)

############################
# 3) 네이버 뉴스 검색 함수
############################
def fetch_naver_news(query: str, display: int = 3, sort: str = "date"):
    """
    네이버 검색 API(뉴스)에서 'query'에 해당하는 뉴스를 가져옵니다.
    display: 가져올 기사 개수 (최대 100).
    sort: 'date' (최신순) 또는 'sim' (정확도/유사도순)
    """
    try:
        client_id = st.secrets["naver"]["client_id"]
        client_secret = st.secrets["naver"]["client_secret"]
    except Exception as e:
        st.error("네이버 API 키가 제대로 설정되지 않았습니다. secrets.toml을 확인하세요.")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    params = {
        "query": query,      # 검색어
        "display": display,  # 가져올 기사 개수
        "sort": sort         # 'date' (최신순), 'sim' (정확도/유사도순)
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("items", [])
    else:
        st.error(f"뉴스 검색 실패 (status code: {response.status_code})")
        return []

############################
# 4) 메인 대시보드 함수
############################
def dashboard_ui():
    # --------------------------
    # 데이터 로드 (현대와 기아)
    # --------------------------
    df_h = load_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    df_k = load_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    if df_h is None or df_k is None:
        st.stop()
    
    # 브랜드 컬럼 추가 후 병합
    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    df = pd.concat([df_h, df_k], ignore_index=True)

    # 월별 컬럼 숫자형 변환
    month_cols = [f"{i}월" for i in range(1, 13)]
    for col in month_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --------------------------
    # 국가명 한글 매핑
    # --------------------------
    country_mapping = {
        "US": "미국", "China": "중국", "Germany": "독일", "Australia": "호주", "Brazil": "브라질",
        "India": "인도", "Canada": "캐나다", "Mexico": "멕시코", "Russia": "러시아", "UK": "영국",
        "EU+EFTA": "유럽연합", "E.Europe/CIS": "동유럽", "Latin America": "중남미",
        "Middle East/Africa": "중동/아프리카", "Asia / Pacific": "아시아/태평양"
    }
    df["국가명_한글"] = df["국가명"].map(country_mapping)
    korean_to_english = {v: k for k, v in country_mapping.items()}

    # --------------------------
    # 차량 구분별 색상 정의
    # --------------------------
    color_map = {
        "Passenger Car": [152, 251, 152, 160],
        "Recreational Vehicle": [255, 165, 0, 160],
        "Commercial Vehicle": [34, 139, 34, 160],
        "Special Vehicle": [220, 20, 60, 160],
        "Total": [100, 100, 100, 100],
    }
    
    # --------------------------
    # 상단 필터 바 구성 (콜 1~6번)
    # --------------------------
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        st.markdown("### Hyundai-Kia ERP")
    with col2:
        st.write("")  # 여백
    with col3:
        st.write("")  # 여백
    with col4:
        year = st.selectbox("연도", sorted(df["연도"].dropna().unique()), key="export_year")
    with col5:
        all_countries = sorted(df["국가명_한글"].dropna().unique())
        country_kor = st.selectbox("국가 (한글)", ["전체"] + all_countries, key="export_country")
    with col6:
        all_vehicle_types = sorted(df["차량 구분"].dropna().unique())
        vehicle_type = st.selectbox("차량 구분", ["전체"] + all_vehicle_types, key="export_vehicle")

    # --------------------------
    # 필터 적용
    # --------------------------
    df_filtered = df[df["연도"] == year].copy()
    if country_kor != "전체":
        eng_country = korean_to_english.get(country_kor)
        df_filtered = df_filtered[df_filtered["국가명"] == eng_country]
    if vehicle_type != "전체":
        df_filtered = df_filtered[df_filtered["차량 구분"] == vehicle_type]

    # 월별 합계 → 총수출량 계산
    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)

    # --------------------------
    # 위치정보 로드 및 병합
    # --------------------------
    loc_df = load_csv("data/세일즈파일/국가_위치정보_수출.csv")
    if loc_df is None:
        st.stop()
    try:
        merged = pd.merge(df_filtered, loc_df, on="국가명", how="left")
        merged = merged.dropna(subset=["위도", "경도", "총수출"])
    except Exception as e:
        st.error(f"위치 정보 병합 중 오류: {e}")
        st.stop()

    # =========================================================
    # 상단 추가 행: 3개 컬럼 (콜 에이, 콜 비, 콜 씨)
    #   - 콜 에이: 여백 (나중에 내용 추가 예정)
    #   - 콜 비: 지도
    #   - 콜 씨: 수출 요약 표
    # =========================================================
    colA, colB, colC = st.columns(3)
    
    with colA:
        st.write("")  # placeholder (여백)

    with colB:
        st.subheader("🗺️ 국가별 수출 지도")
        if len(merged) == 0:
            st.warning("표시할 지도 데이터가 없습니다. 필터를 바꿔보세요.")
        else:
            color = color_map.get(vehicle_type, [173, 216, 230, 160])
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1.3),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=merged,
                        get_position='[경도, 위도]',
                        get_radius='총수출 / 0.5',
                        get_fill_color=f"[{color[0]}, {color[1]}, {color[2]}, 160]",
                        pickable=True
                    )
                ],
                tooltip={"text": "{국가명_한글}\n차량: {차량 구분}\n수출량: {총수출} 대"}
            ))

    with colC:
        st.subheader("📦 국가별 수출 요약")
        # 표 스타일 (테두리, 라운드 효과)
        st.markdown("""
            <style>
            table {
                width: 100% !important;
                table-layout: fixed;
                border: 2px solid #000 !important;
                border-radius: 10px !important;
                border-collapse: separate;
                overflow: hidden;
            }
            </style>
            """, unsafe_allow_html=True)

        top_table = merged.sort_values("총수출", ascending=False).head(3)
        bottom_table = merged.sort_values("총수출").head(3)

        # 상위 수출국 표
        top_display = top_table[['국가명_한글', '차량 구분', '총수출']].reset_index(drop=True)
        top_styled = (
            top_display.style
            .set_caption("상위 수출국")
            .set_table_styles([
                {
                    'selector': 'caption',
                    'props': [
                        ('font-size', '24px'),
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('margin-bottom', '10px')
                    ]
                },
                {
                    'selector': 'thead th',
                    'props': [
                        ('background-color', '#FAF2D0'),
                        ('text-align', 'center'),
                        ('padding', '8px')
                    ]
                },
                {
                    'selector': 'tbody td',
                    'props': [
                        ('background-color', 'transparent'),
                        ('text-align', 'center'),
                        ('padding', '8px')
                    ]
                }
            ])
            .format({'총수출': '{:,}'})
            .hide(axis="index")
        )
        html_top = top_styled.to_html()

        # 하위 수출국 표
        bottom_display = bottom_table[['국가명_한글', '차량 구분', '총수출']].reset_index(drop=True)
        bottom_styled = (
            bottom_display.style
            .set_caption("하위 수출국")
            .set_table_styles([
                {
                    'selector': 'caption',
                    'props': [
                        ('font-size', '24px'),
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('margin-bottom', '10px')
                    ]
                },
                {
                    'selector': 'thead th',
                    'props': [
                        ('background-color', '#FAF2D0'),
                        ('text-align', 'center'),
                        ('padding', '8px')
                    ]
                },
                {
                    'selector': 'tbody td',
                    'props': [
                        ('background-color', 'transparent'),
                        ('text-align', 'center'),
                        ('padding', '8px')
                    ]
                }
            ])
            .format({'총수출': '{:,}'})
            .hide(axis="index")
        )
        html_bottom = bottom_styled.to_html()

        st.markdown(html_top, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown(html_bottom, unsafe_allow_html=True)

    # =========================================================
    # 하단 추가 행: 2개 컬럼 (콜 레프트, 콜 라이트)
    #   - 콜 레프트: 여백 (나중에 내용 추가 예정)
    #   - 콜 라이트: 뉴스 기사 (총 3개, 최신순, 타이틀+본문 요약)
    # =========================================================
    colLeft, colRight = st.columns([1, 1])
    
    with colLeft:
        st.write("")  # placeholder (여백)
    
    with colRight:
        st.subheader("자동차 관련 최신 뉴스")
        # 예시 쿼리: "국내차량 해외 반응"
        articles = fetch_naver_news(query="국내차량 해외 반응", display=3, sort="date")
        if not articles:
            st.write("관련 뉴스를 찾을 수 없습니다.")
        else:
            for article in articles:
                title = remove_html_tags(article.get("title", ""))
                description = remove_html_tags(article.get("description", ""))
                link = article.get("link", "#")
                # 본문은 70자까지만 표시
                if len(description) > 70:
                    description = description[:70] + "..."
                st.markdown(f"**[{title}]({link})**")
                st.markdown(description)
                st.markdown("---")
    
    st.markdown("---")

