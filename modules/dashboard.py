import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import altair as alt
from modules.dashboard_data_loader import load_and_merge_car_data, load_and_merge_export_data, load_and_merge_plant_data
from modules.dashboard_news import fetch_naver_news, render_news_results
from modules.dashboard_charts import render_hyundai_chart, render_kia_chart, render_export_map, render_top_bottom_summary
from modules.dashboard_filter import render_filter_options
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
import urllib3
import re
import os
import plotly.express as px
import requests


# 이전 평일 계산 함수
def get_previous_weekday(date):
    one_day = timedelta(days=1)
    while True:
        date -= one_day
        if date.weekday() < 5:
            return date

# 환율 데이터 조회 함수
def fetch_exim_exchange(date, api_key):
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        "authkey": api_key,
        "searchdate": date.strftime("%Y%m%d"),
        "data": "AP01"
    }
    try:
        response = requests.get(url, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        st.error(f"\u2757 API 호출 오류: {e}")
        return None


def dashboard_ui():
    st.markdown("""
        <div style='padding: 15px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px;'>
            <img src='https://m.ddaily.co.kr/2022/07/28/2022072820411931122_l.png' alt='Hyundai Kia Logo' style='height: 50px;' />
            <h1 style='margin: 0; font-size: 1.8em;'>Hyundai & Kia Export Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)


    #데이터 로드 및 병합
    df_region = load_and_merge_export_data()
    if df_region is None:
        st.error("수출 데이터 로드 실패")
        st.stop()
    df_car = load_and_merge_car_data()
    if df_car is None:
        st.error("차종 데이터 로드 실패")
        st.stop()
    df_plant = load_and_merge_plant_data()
    if df_plant is None:
        st.error("공장 데이터 로드 실패")
        st.stop()

    year, company = render_filter_options(df_region, df_car, df_plant)
    month_cols = [col for col in df_region.columns if str(year) in col and "-" in col]

    new_df_region = df_region.copy()
    new_df_region["총수출"] = new_df_region[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        new_df_region = new_df_region[new_df_region["브랜드"] == company]
    else:
        new_df_region["지역명"] = new_df_region["지역명"].apply(
            lambda x: "동유럽 및 구소련" if "구소련" in x else ("유럽" if "유럽" in x else x)
        )

    colA, colB, colC = st.columns([2.15, 1.85, 3.5])

    with colA:
        render_hyundai_chart(year)
    with colB:
        render_kia_chart(year)
    with colC:
        render_top_bottom_summary(new_df_region, company, year)

    # 데이터 시각화 전처리
    start_col = f"{year}-01"
    end_col = f"{year}-12"
    df_filtered = pd.concat([new_df_region.iloc[:, 0], new_df_region.loc[:, start_col:end_col]], axis = 1)
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
    grouped_monthly["순위_top"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=False).astype(int)
    top_df = grouped_monthly[grouped_monthly["순위_top"] <= 3].sort_values(["월", "순위_top"])

    # Bottom 3
    grouped_monthly["순위_bottom"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=True).astype(int)
    bottom_df = grouped_monthly[grouped_monthly["순위_bottom"] <= 3].sort_values(["월", "순위_bottom"])

    colD, colE = st.columns([1, 1])

    with colD:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#ede7f6; border-radius:10px;'>
            <h4>월별 Top 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_top = px.bar(top_df, x="월", y="수출량", color="지역명", barmode="group",
                        labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                        height=400)
        st.plotly_chart(fig_top, use_container_width=True)

        with st.expander("원본 데이터 보기", expanded=False):
            st.dataframe(top_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    with colE:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#f0f4c3; border-radius:10px;'>
            <h4>월별 Bottom 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_bottom = px.bar(bottom_df, x="월", y="수출량", color="지역명", barmode="group",
                            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                            height=400)
        st.plotly_chart(fig_bottom, use_container_width=True)

        with st.expander("원본 데이터 보기", expanded=False):
            st.dataframe(bottom_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)


    col_left, col_right = st.columns([1, 1])

    with col_left:
        # 월별 국가별 판매량 변화 추이 (라인 차트)
        st.markdown("""
        <div style='margin-top:30px; padding:10px; background-color:#e3f2fd; border-radius:10px;'>
            <h4>월별 국가별 판매량 변화 추이</h4>
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
            <h4>국가별 {year}년 판매량 데이터</h4>
        </div>
        """, unsafe_allow_html=True)
        st.text("")
        st.dataframe(new_df, hide_index=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
            <div style='background-color:#e3f2fd;padding:10px;border-radius:12px;margin-top:40px;'>
                <h4>국가별 실시간 환율 조회 </h4>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        # API 키 로드
        try:
            api_key = st.secrets["exim"]["apikey"]
        except KeyError:
            st.error("❌ API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`을 확인해주세요.")
            st.stop()

        # 날짜 선택 UI
        now = datetime.now()
        default_date = get_previous_weekday(now) if now.weekday() >= 5 or now.hour < 11 else now
        selected_date = st.date_input("환율 조회 날짜", default_date.date(), max_value=datetime.today())
        query_date = datetime.combine(selected_date, datetime.min.time())

        # API 호출 및 데이터 처리
        data = fetch_exim_exchange(query_date, api_key)
        if not data or not isinstance(data, list):
            st.warning("⚠️ 해당 날짜의 환율 데이터를 가져올 수 없습니다.")
            st.stop()

        # 데이터프레임 생성
        all_rows = []
        for row in data:
            if isinstance(row, dict) and row.get("result") == 1:
                try:
                    rate = float(row["deal_bas_r"].replace(",", ""))
                    all_rows.append({
                        "통화": row.get("cur_unit"),
                        "통화명": row.get("cur_nm"),
                        "환율": rate
                    })
                except Exception as e:
                    st.warning(f"데이터 처리 중 오류 발생: {e}")
                    continue

        if not all_rows:
            st.warning("❗ 처리된 환율 데이터가 없습니다.")
            st.stop()

        # 기본 국가 리스트
        default_countries = ['KRW', 'USD', 'JPY', 'CNY', 'EUR', 'GBP', 'AUD', 'CAD', 'CHF', 'HKD']
        
        # 모든 통화 리스트 생성
        all_currencies = [row['통화'] for row in all_rows]
        
        # 사용자가 추가로 선택할 수 있는 통화 리스트
        additional_currencies = [curr for curr in all_currencies if curr not in default_countries]
        
        # 사용자 선택 UI
        selected_additional = st.multiselect("추가로 표시할 통화를 선택하세요:", additional_currencies)
        
        # 표시할 통화 리스트 생성
        display_currencies = default_countries + selected_additional

        # 표시할 통화만 필터링
        df_display = pd.DataFrame([row for row in all_rows if row['통화'] in display_currencies])
        df_display = df_display.sort_values('통화')

        # 전날 환율 데이터 (실제로는 API나 데이터베이스에서 가져와야 함)
        previous_day_rates = {row['통화']: row['환율'] * 0.99 for row in all_rows}  # 예시로 1% 낮은 값 사용

        # 전날 환율과 변동 계산
        df_display['전날 환율'] = df_display['통화'].map(previous_day_rates)
        df_display['변동'] = df_display['환율'] - df_display['전날 환율']

        # 삼각표 생성
        def triangular_indicator(change):
            if change > 0:
                return '<span style="color: red;">▲</span>'
            elif change < 0:
                return '<span style="color: blue;">▼</span>'
            else:
                return '<span style="color: gray;">▶</span>'

        df_display['등락'] = df_display['변동'].apply(triangular_indicator)

        # 표시할 열 선택 및 재정렬
        df_display = df_display[['통화', '통화명', '환율', '전날 환율', '변동', '등락']]

        # 스타일 적용 및 표시
        styled_df = df_display.style.format({
            '환율': '{:,.2f} KRW',
            '전날 환율': '{:,.2f} KRW',
            '변동': '{:+,.2f} KRW'
        }).hide(axis="index").set_properties(**{
            'background-color': '#f0f2f6',
            'color': 'black',
            'border-color': 'white',
            'text-align': 'center',
            'padding': '12px'  
        }).set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#4e73df'),
                ('color', 'white'),
                ('padding', '14px'), 
                ('font-size', '16px')
            ]},
            {'selector': 'td', 'props': [
                ('padding', '12px'),  
                ('font-size', '15px')
            ]},
            {'selector': 'tr:hover', 'props': [
                ('background-color', '#e8eaf6')
            ]}
        ])

        # Streamlit에서 HTML로 렌더링
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)


    with col2:
        with st.container():
            st.markdown("""
                <div style='background-color:#e3f2fd;padding:10px;border-radius:12px;margin-top:40px;'>
                <h4>현대차 수출 관련 뉴스</h4>
            """, unsafe_allow_html=True)

            st.write("")

            news_data = fetch_naver_news("현대차 수출", display=4)
            if news_data:
                render_news_results(news_data)
            st.markdown("</div>", unsafe_allow_html=True)