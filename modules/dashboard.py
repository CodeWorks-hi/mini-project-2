import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import altair as alt
from modules.dashboard_kpi import calculate_kpis, render_kpi_card
from modules.dashboard_data_loader import load_and_merge_export_data, load_location_data
from modules.dashboard_news import fetch_naver_news, render_news_results
from modules.dashboard_charts import render_hyundai_chart, render_kia_chart, render_export_map, render_top_bottom_summary
from modules.dashboard_filter import render_filter_options
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup

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
    df = load_and_merge_export_data()
    if df is None:
        st.error("수출 데이터 로드 실패")
        st.stop()

    color_map = {
        "Passenger Car": [152, 251, 152, 160],
        "Recreational Vehicle": [255, 165, 0, 160],
        "Commercial Vehicle": [34, 139, 34, 160],
        "Special Vehicle": [220, 20, 60, 160],
        "기타": [173, 216, 230, 160]
    }

    # KPI + 필터 카드
    col1, col2 = st.columns([2,4])
    with col1:
        year, country_kor, vehicle_type = render_filter_options(df)
    with col2:
        st.markdown("---")
        month_cols = [col for col in df.columns if str(year) in col and "-" in col]

        df_filtered = df.copy()
        df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
        if country_kor != "전체":
            df_filtered = df_filtered[df_filtered["지역명"] == country_kor]
        if vehicle_type != "전체":
            df_filtered = df_filtered[df_filtered["차량 구분"] == vehicle_type]

        df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
        kpi1, kpi2, kpi3 = calculate_kpis(df_filtered, month_cols, brand="전체", country=country_kor, vehicle_type=vehicle_type)
        render_kpi_card(kpi1, kpi2, kpi3)
        st.markdown("---")


    loc_df = load_location_data()
    if loc_df is None:
        st.error("위치 정보 로드 실패")
        st.stop()
    try:
        merged = pd.merge(df_filtered, loc_df, on="지역명", how="left")
        merged = merged.dropna(subset=["위도", "경도", "총수출"])
    except Exception as e:
        st.error(f"위치 정보 병합 중 오류: {e}")
        st.stop()

    colA, colB, colC, colD = st.columns([2.4, 2, 3, 1.8])

    with colA:
        render_hyundai_chart(year)
    with colB:
        render_kia_chart(year)
    with colC:
        render_export_map(merged, vehicle_type, color_map)
    with colD:
        render_top_bottom_summary(merged)

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
