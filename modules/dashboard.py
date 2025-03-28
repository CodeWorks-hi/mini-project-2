import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import altair as alt
from modules.dashboard_kpi import calculate_kpis, render_kpi_card
from modules.dashboard_data_loader import load_and_merge_export_data
from modules.dashboard_news import fetch_naver_news, render_news_results
from modules.dashboard_charts import render_hyundai_chart, render_kia_chart, render_export_map, render_top_bottom_summary
from modules.dashboard_filter import render_filter_options
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
import os
import plotly.express as px

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

    #데이터 로드 및 병합
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
    col1, col2 = st.columns([1, 1])
    with col1:
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
    with col2:
        year, company = render_filter_options(df)
        month_cols = [col for col in df.columns if str(year) in col and "-" in col]

        df_filtered = df.copy()
        df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
        if company != "전체":
            df_filtered = df_filtered[df_filtered["브랜드"] == company]
        else:
            df_filtered["지역명"] = df_filtered["지역명"].apply(
                lambda x: "동유럽 및 구소련" if "구소련" in x else ("유럽" if "유럽" in x else x)
            )

    colA, colB, colC = st.columns([2.15, 1.85, 3.5])

    with colA:
        render_hyundai_chart(year)
    with colB:
        render_kia_chart(year)
    with colC:
        render_top_bottom_summary(df_filtered, company, year)

    # 데이터 시각화 전처리
    start_col = f"{year}-01"
    end_col = f"{year}-12"
    df_filtered = pd.concat([df_filtered.iloc[:, 0], df_filtered.loc[:, start_col:end_col]], axis = 1)
    merged_df = df_filtered[df_filtered.loc[:, start_col:end_col].fillna(0).sum(axis=1) > 0]
    new_df = merged_df.copy()

    monthly_data = []

    # 총수출 시각화용 컬럼 생성
    merged_df["총수출"] = merged_df.loc[:, start_col:end_col].sum(axis=1)
    for month in pd.date_range(start=start_col, end=end_col, freq='MS').strftime('%Y-%m'):
        if month in merged_df.columns:
            month_data = merged_df[["지역명", month]].copy()
            month_data = month_data.dropna()
            month_data = month_data[month_data[month] > 0]
            month_data["월"] = month
            month_data.rename(columns={month: "수출량"}, inplace=True)
            monthly_data.append(month_data)

    monthly_df = pd.concat(monthly_data).reset_index(drop=True)

    # 월별 국가별 수출량 집계
    grouped_monthly = (
        monthly_df.groupby(["월", "지역명"], as_index=False)["수출량"]
        .sum()
        .sort_values(["월", "수출량"], ascending=[True, False])
    )

    # Top 3
    grouped_monthly["순위"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=False).astype(int)
    top_df = grouped_monthly[grouped_monthly["순위"] <= 3].sort_values(["월", "순위"])

    # Bottom 3
    grouped_monthly["순위_bottom"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=True).astype(int)
    bottom_df = grouped_monthly[grouped_monthly["순위_bottom"] <= 3].sort_values(["월", "순위_bottom"])
    bottom_df.drop(columns=["순위_bottom"], inplace=True)

    colD, colE = st.columns([1, 1])

    with colD:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#ede7f6; border-radius:10px;'>
            <h4>📊 월별 Top 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_top = px.bar(top_df, x="월", y="수출량", color="지역명", barmode="group",
                        labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                        height=400)
        st.plotly_chart(fig_top, use_container_width=True)

        with st.expander("📋 원본 데이터 보기", expanded=False):
            st.dataframe(top_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    with colE:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#f0f4c3; border-radius:10px;'>
            <h4>📊 월별 Bottom 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_bottom = px.bar(bottom_df, x="월", y="수출량", color="지역명", barmode="group",
                            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                            height=400)
        st.plotly_chart(fig_bottom, use_container_width=True)

        with st.expander("📋 원본 데이터 보기", expanded=False):
            st.dataframe(bottom_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)


    col_left, col_right = st.columns([1, 1])

    with col_left:
        # 📈 월별 국가별 판매량 변화 추이 (라인 차트)
        st.markdown("""
        <div style='margin-top:30px; padding:10px; background-color:#e3f2fd; border-radius:10px;'>
            <h4>📈 월별 국가별 판매량 변화 추이</h4>
        </div>
        """, unsafe_allow_html=True)

        # 월별 컬럼만 추출
        month_cols = pd.date_range(start=start_col, end=end_col, freq='MS').strftime('%Y-%m')

        # melt 전에 국가별로 월별 합계 집계
        aggregated = merged_df.groupby("지역명")[month_cols].sum().reset_index()

        # 그 후 melt
        line_df = aggregated.melt(
            id_vars="지역명",
            value_vars=month_cols,
            var_name="월", value_name="수출량"
        )
        line_df = line_df.dropna()
        line_df = line_df[line_df["수출량"] > 0]

        fig_line = px.line(
            line_df,
            x="월", y="수출량", color="지역명",
            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
            markers=True,
            height=500
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.markdown(f"""
        <div style='margin-top:30px; padding:10px; background-color:#f5f5f5; border-radius:10px;'>
            <h4>🗂️ 국가별 {year}년 판매량 데이터</h4>
        </div>
        """, unsafe_allow_html=True)
        st.text("")
        st.dataframe(new_df, hide_index=True)

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
