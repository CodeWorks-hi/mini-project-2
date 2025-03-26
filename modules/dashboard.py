import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import re
import altair as alt
from datetime import datetime
from modules.dashboard_kpi import calculate_kpis, render_kpi_cards
from modules.dashboard_filter import get_filter_options, apply_filters
from modules.dashboard_news import fetch_naver_news, render_news_results


@st.cache_data
def load_csv(path):
    """CSV 파일 로드 함수"""
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
        return None

def dashboard_ui():
    """대시보드 메인 UI"""
    
    # 상단 제목 및 로고
    st.markdown("""
        <style>
        .title-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .title-container img {
            width: 100px;
        }
        .title-container h1 {
            font-size: 1.8rem;
            margin: 0;
        }
        </style>
        <div class="title-container">
            <h1>📊  Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)

    # 데이터 불러오기
    df_h = load_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    df_k = load_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    if df_h is None or df_k is None:
        st.error("CSV 파일을 불러올 수 없습니다.")
        st.stop()

    
    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"

    # 🚨 현대에는 차량 구분이 없으므로 기본값 추가
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"

    # 병합
    df = pd.concat([df_h, df_k], ignore_index=True)

    # 월별 컬럼 숫자형 변환
    month_cols = [f"{i}월" for i in range(1, 13)]
    for col in month_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --------------------------
    # 차량 구분별 색상 정의
    # --------------------------
    color_map = {
        "Passenger Car": [152, 251, 152, 160],
        "Recreational Vehicle": [255, 165, 0, 160],
        "Commercial Vehicle": [34, 139, 34, 160],
        "Special Vehicle": [220, 20, 60, 160],
        "기타": [173, 216, 230, 160]
    }

    # --------------------------
    # 상단 필터 바
    # --------------------------
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        st.write("")
    with col2:
        st.write("")
    with col3:
        st.write("")
    with col4:
        year = st.selectbox("연도", sorted(df["연도"].dropna().unique()), key="export_year")
    with col5:
        all_countries = sorted(df["지역명"].dropna().unique())
        country_kor = st.selectbox("국가 (지역명)", ["전체"] + all_countries, key="export_country")
    with col6:
        all_vehicle_types = sorted(df["차량 구분"].dropna().unique())
        vehicle_type = st.selectbox("차량 구분", ["전체"] + all_vehicle_types, key="export_vehicle")

    # --------------------------
    # 필터 적용
    # --------------------------
    df_filtered = df[df["연도"] == year].copy()
    if country_kor != "전체":
        df_filtered = df_filtered[df_filtered["지역명"] == country_kor]
    if vehicle_type != "전체":
        df_filtered = df_filtered[df_filtered["차량 구분"] == vehicle_type]

    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)

    # KPI 카드 섹션
    kpi1 = int(df_filtered[month_cols].sum().sum())
    kpi2 = df_filtered["브랜드"].nunique()
    kpi3 = df_filtered["지역명"].nunique()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 수출량", f"{kpi1:,} 대")
    
    with col2:
        st.metric("브랜드 수", kpi2)
    
    with col3:
        st.metric("수출 국가 수", kpi3)

    # --------------------------
    # 위치정보 병합 (지역명 기준)
    # --------------------------
    loc_df = load_csv("data/세일즈파일/지역별_위치정보.csv")
    if loc_df is None:
        st.stop()
    try:
        merged = pd.merge(df_filtered, loc_df, on="지역명", how="left")
        merged = merged.dropna(subset=["위도", "경도", "총수출"])
    except Exception as e:
        st.error(f"위치 정보 병합 중 오류: {e}")
        st.stop()



    # =========================================================
    # 상단: 지도 + 수출 요약 표
    # =========================================================
    colA, colB, colC = st.columns([4,3,2])
    
    with colA:

        # --------------------------
        # 생산 데이터 로드 및 전처리
        # --------------------------
        def load_data():
            hyundai = pd.read_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
            kia = pd.read_csv("data/processed/기아_해외공장판매실적_전처리.CSV")
            hyundai["브랜드"] = "현대"
            kia["브랜드"] = "기아"
            return pd.concat([hyundai, kia], ignore_index=True)

        month_cols = [f"{i}월" for i in range(1, 13)]
        prod_df = load_data()
        prod_df[month_cols] = prod_df[month_cols].apply(pd.to_numeric, errors="coerce")


        # --------------------------
        # 연도 필터만 적용 (전체 공장 포함)
        # --------------------------
        prod_df = prod_df[prod_df["연도"] == year]

        # --------------------------
        # 공장별 총생산 계산 (브랜드와 공장명(국가) 기준)
        # --------------------------
        factory_grouped = prod_df.groupby(["브랜드", "공장명(국가)"])[month_cols].sum(numeric_only=True)
        factory_grouped["총생산"] = factory_grouped.sum(axis=1)
        factory_grouped = factory_grouped.reset_index()

        # --------------------------
        # 현대와 기아를 비교하는 차트 생성
        # Y축: 공장명(국가)의 유니크 값 (전체 공장)
        # X축: 해당 공장에 대한 총생산 (모든 월 합계)
        # 색상: 브랜드
        # --------------------------
        if factory_grouped.empty:
            st.warning("선택한 연도에 해당하는 생산 데이터가 없습니다.")
        else:
            chart = alt.Chart(factory_grouped).mark_bar().encode(
                x=alt.X("총생산:Q", title="총 생산량"),
                y=alt.Y("공장명(국가):N", sort="-x", title="공장"),
                color="브랜드:N"
            ).properties(
                width=420,
                height=420,
                title="공장별 총 생산량 비교 (현대 + 기아)"
            )
            st.altair_chart(chart, use_container_width=True)

    with colB:
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
                tooltip={"text": "{지역명}\n차량: {차량 구분}\n수출량: {총수출} 대"}
            ))

    with colC:
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

        top_display = top_table[['지역명', '차량 구분', '총수출']].reset_index(drop=True)
        bottom_display = bottom_table[['지역명', '차량 구분', '총수출']].reset_index(drop=True)

        top_styled = (
            top_display.style
            .set_caption("상위 수출국")
            .format({'총수출': '{:,}'})
            .hide(axis="index")
        )
        bottom_styled = (
            bottom_display.style
            .set_caption("하위 수출국")
            .format({'총수출': '{:,}'})
            .hide(axis="index")
        )

        st.markdown(top_styled.to_html(), unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown(bottom_styled.to_html(), unsafe_allow_html=True)

    # =========================================================
    # 하단: 뉴스 섹션
    # =========================================================
    # 하단 뉴스 섹션
    st.subheader("📰 관련 뉴스")
    
    news_data = fetch_naver_news("현대차 수출", display=4)
    
    if news_data:
        render_news_results(news_data)

    st.markdown("---")
