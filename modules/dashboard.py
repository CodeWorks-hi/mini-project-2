import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import altair as alt
from modules.dashboard_kpi import calculate_kpis, render_kpi_cards
from modules.dashboard_filter import get_filter_options, apply_filters
from modules.dashboard_news import fetch_naver_news, render_news_results
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
        return None

def get_previous_weekday(date):
    one_day = timedelta(days=1)
    while True:
        date -= one_day
        if date.weekday() < 5:
            return date

def get_exchange_rate(currency_code):
    url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_{currency_code}KRW"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rate_info = soup.find('p', class_='no_today').get_text(strip=True)
        change_icon = soup.find('span', class_='ico')
        change_sign = '▲' if change_icon and 'up' in change_icon['class'] else '▼' if change_icon and 'down' in change_icon['class'] else ''
        return f"{currency_code}: {rate_info} KRW | 변동: {change_sign}"
    except Exception as e:
        return f"❗ 데이터 가져오기 실패: {e}"

def dashboard_ui():
    st.markdown("""
        <div style='padding: 15px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='margin: 0;'>📊 Hyundai & Kia Export Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)

    # 환율 정보 카드
    with st.container():
        st.markdown("""
            <div style='padding: 10px; background-color: #e8f0fe; border-radius: 10px; margin-bottom: 15px;'>
                <h4>💱 실시간 환율 (네이버 기준)</h4>
        """, unsafe_allow_html=True)

        exchange_rate_placeholder = st.empty()
        currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP']
        for currency in currencies:
            rate_info = get_exchange_rate(currency)
            exchange_rate_placeholder.markdown(f"<div style='margin-bottom: 5px;'>🪙 {rate_info}</div>", unsafe_allow_html=True)

        st.markdown("""</div>""", unsafe_allow_html=True)

    # 데이터 로드 및 병합
    df_h = load_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    df_k = load_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    if df_h is None or df_k is None:
        st.error("CSV 파일을 불러올 수 없습니다.")
        st.stop()

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"
    df = pd.concat([df_h, df_k], ignore_index=True)

    month_cols = [f"{i}월" for i in range(1, 13)]
    for col in month_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    color_map = {
        "Passenger Car": [152, 251, 152, 160],
        "Recreational Vehicle": [255, 165, 0, 160],
        "Commercial Vehicle": [34, 139, 34, 160],
        "Special Vehicle": [220, 20, 60, 160],
        "기타": [173, 216, 230, 160]
    }

    # KPI + 필터 카드
    st.markdown("""
        <div style='padding: 10px; background-color: #f0f7ec; border-radius: 10px; margin-bottom: 15px;'>
            <h4>🎯 필터 및 주요 지표</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        year = st.selectbox("연도", sorted(df["연도"].dropna().unique()), key="export_year")
    with col2:
        all_countries = sorted(df["지역명"].dropna().unique())
        country_kor = st.selectbox("국가 (지역명)", ["전체"] + all_countries, key="export_country")
    with col3:
        all_vehicle_types = sorted(df["차량 구분"].dropna().unique())
        vehicle_type = st.selectbox("차량 구분", ["전체"] + all_vehicle_types, key="export_vehicle")

    df_filtered = df[df["연도"] == year].copy()
    if country_kor != "전체":
        df_filtered = df_filtered[df_filtered["지역명"] == country_kor]
    if vehicle_type != "전체":
        df_filtered = df_filtered[df_filtered["차량 구분"] == vehicle_type]

    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    kpi1 = int(df_filtered[month_cols].sum().sum())
    kpi2 = df_filtered["브랜드"].nunique()
    kpi3 = df_filtered["지역명"].nunique()

    with col4:
        st.markdown("#### 🚗 총 수출량")
        st.metric(label="", value=f"{kpi1:,} 대")
    with col5:
        st.markdown("#### 🏢 브랜드 수")
        st.metric(label="", value=kpi2)
    with col6:
        st.markdown("#### 🌍 수출 국가 수")
        st.metric(label="", value=kpi3)

    st.markdown("""</div>""", unsafe_allow_html=True)
    st.divider()

    # 위치정보 병합
    loc_df = load_csv("data/세일즈파일/지역별_위치정보.csv")
    if loc_df is None:
        st.stop()
    try:
        merged = pd.merge(df_filtered, loc_df, on="지역명", how="left")
        merged = merged.dropna(subset=["위도", "경도", "총수출"])
    except Exception as e:
        st.error(f"위치 정보 병합 중 오류: {e}")
        st.stop()

    # 지도 + 차트 + 요약 카드
    colA, colB, colC = st.columns([4, 3, 2])

    with colA:
        st.markdown("""
        <div style='background-color:#f3f4f6;padding:20px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,0.05);'>
        <h4>🏭 공장별 생산량 차트</h4>
        """, unsafe_allow_html=True)

        def load_data():
            hyundai = pd.read_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
            kia = pd.read_csv("data/processed/기아_해외공장판매실적_전처리.CSV")
            hyundai["브랜드"] = "현대"
            kia["브랜드"] = "기아"
            return pd.concat([hyundai, kia], ignore_index=True)

        prod_df = load_data()
        prod_df[month_cols] = prod_df[month_cols].apply(pd.to_numeric, errors="coerce")
        prod_df = prod_df[prod_df["연도"] == year]
        factory_grouped = prod_df.groupby(["브랜드", "공장명(국가)"])[month_cols].sum(numeric_only=True)
        factory_grouped["총생산"] = factory_grouped.sum(axis=1)
        factory_grouped = factory_grouped.reset_index()

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

        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("""
            <div style='background-color:#f9fbe7;padding:15px;border-radius:12px;margin-bottom:20px;'>
            <h4>🗺️ 수출 국가별 지도</h4>
        """, unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

    with colC:
        st.markdown("""
        <div style='background-color:#ede7f6;padding:15px;border-radius:12px;margin-bottom:20px;'>
        <h5>📦 수출 상하위 국가 요약</h4>
        """, unsafe_allow_html=True)

        top_table = merged.sort_values("총수출", ascending=False).head(3)
        bottom_table = merged.sort_values("총수출").head(3)
        top_display = top_table[['지역명', '차량 구분', '총수출']].reset_index(drop=True)
        bottom_display = bottom_table[['지역명', '차량 구분', '총수출']].reset_index(drop=True)

        st.dataframe(top_display.style.format({'총수출': '{:,}'}), use_container_width=True)
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.dataframe(bottom_display.style.format({'총수출': '{:,}'}), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # 뉴스 섹션
    with st.container():
        st.markdown("""
            <div style='background-color:#e3f2fd;padding:10px;border-radius:12px;margin-top:40px;'>
            <h4>📰 현대차 수출 관련 뉴스</h4>
        """, unsafe_allow_html=True)

        news_data = fetch_naver_news("현대차 수출", display=4)
        if news_data:
            render_news_results(news_data)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
