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


def dashboard_ui():
    st.markdown("""
        <div style='padding: 15px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px;'>
            <img src='https://m.ddaily.co.kr/2022/07/28/2022072820411931122_l.png' alt='Hyundai Kia Logo' style='height: 50px;' />
            <h1 style='margin: 0; font-size: 1.8em;'>Hyundai & Kia Export Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)

    # 1) 데이터 로드
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

    # 2) 필터
    year, company = render_filter_options(df_region, df_car, df_plant)
    month_cols = [col for col in df_region.columns if str(year) in col and "-" in col]

    # 3) 전처리
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

    month_cols = [col for col in new_df_region.columns if col.startswith(f"{year}-")]
    if not month_cols:
        st.warning(f"{year}년의 월별 데이터가 없습니다.")
        st.stop()

    df_filtered = pd.concat([new_df_region.iloc[:, 0], new_df_region[month_cols]], axis=1)
    merged_df = df_filtered[df_filtered[month_cols].fillna(0).sum(axis=1) > 0].copy()

    merged_df["총수출"] = merged_df[month_cols].sum(axis=1)

    monthly_data = []
    for month in month_cols:
        mdata = merged_df[["지역명", month]].copy()
        mdata.dropna(inplace=True)
        mdata = mdata[mdata[month] > 0]
        mdata["월"] = month
        mdata.rename(columns={month: "수출량"}, inplace=True)
        monthly_data.append(mdata)

    monthly_df = pd.concat(monthly_data).reset_index(drop=True)
    grouped_monthly = (
        monthly_df.groupby(["월", "지역명"], as_index=False)["수출량"]
        .sum()
        .sort_values(["월", "수출량"], ascending=[True, False])
    )

    grouped_monthly["순위_top"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=False).astype(int)
    top_df = grouped_monthly[grouped_monthly["순위_top"] <= 3].sort_values(["월", "순위_top"])

    grouped_monthly["순위_bottom"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=True).astype(int)
    bottom_df = grouped_monthly[grouped_monthly["순위_bottom"] <= 3].sort_values(["월", "순위_bottom"])

    colD, colE = st.columns([1, 1])
    with colD:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#ede7f6; border-radius:10px;'>
            <h4>월별 Top 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_top = px.bar(
            top_df, x="월", y="수출량", color="지역명", barmode="group",
            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
            height=400
        )
        st.plotly_chart(fig_top, use_container_width=True)

        with st.expander("원본 데이터 보기", expanded=False):
            st.dataframe(top_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    with colE:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#f0f4c3; border-radius:10px;'>
            <h4>월별 Bottom 3 수출 국가</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_bottom = px.bar(
            bottom_df, x="월", y="수출량", color="지역명", barmode="group",
            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
            height=400
        )
        st.plotly_chart(fig_bottom, use_container_width=True)

        with st.expander("원본 데이터 보기", expanded=False):
            st.dataframe(bottom_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    col_left, col_right = st.columns([1, 1.2])
    with col_left:
        st.markdown("""
        <div style='margin-top:30px; padding:10px; background-color:#e3f2fd; border-radius:10px;'>
            <h4>월별 국가별 판매량 변화 추이</h4>
        </div>
        """, unsafe_allow_html=True)

        # 지역명별 월별 수출량
        aggregated = merged_df.groupby("지역명")[month_cols].sum().reset_index()
        line_df = aggregated.melt(
            id_vars="지역명",
            value_vars=month_cols,
            var_name="월", value_name="수출량"
        )
        line_df.dropna(subset=["수출량"], inplace=True)
        line_df = line_df[line_df["수출량"] > 0]

        fig_line = px.line(
            line_df, x="월", y="수출량", color="지역명",
            labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
            markers=True, height=500
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.markdown(f"""
        <div style='margin-top:30px; padding:10px; background-color:#f5f5f5; border-radius:10px;'>
            <h4>국가별 {year}년 판매량 데이터</h4>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.dataframe(merged_df, hide_index=True)

    # 하단: 왼쪽(뉴스), 오른쪽(환율) 등등 원하는 레이아웃

    st.markdown("""
        <div style='background-color:#e3f2fd;padding:10px;border-radius:12px;margin-top:40px;'>
         <h4>현대차 수출 관련 뉴스</h4>
        """, unsafe_allow_html=True)

    st.write("")

    from modules.dashboard_news import fetch_naver_news, render_news_results
    news_data = fetch_naver_news("현대차 수출", display=4)
    if news_data:
        render_news_results(news_data)
    else:
        st.warning("현대차 관련 뉴스를 가져오지 못했습니다.")
    st.markdown("</div>", unsafe_allow_html=True)