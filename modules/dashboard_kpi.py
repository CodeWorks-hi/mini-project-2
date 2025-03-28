# modules/dashboard_kpi.py
# ----------------------------
# 대시보드 KPI 카드 렌더링 모듈
# - 핵심 성과 지표 시각화
# - 동적 스타일링 및 인터랙티브 요소
# ----------------------------

import streamlit as st
import pandas as pd

def calculate_kpis(df: pd.DataFrame, month_cols: list, brand: str = "전체", country: str = "전체"):
    # 연도 필터링을 마친 상태의 df를 받아서 KPI 계산
    df_filtered = df.copy()

    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]
    if country != "전체":
        df_filtered = df_filtered[df_filtered["지역명"] == country]

    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    total_export = int(df_filtered[month_cols].sum().sum())
    brand_count = df_filtered["브랜드"].nunique()
    country_count = df_filtered["지역명"].nunique()

    return total_export, brand_count, country_count

def render_kpi_card(total_export: int, brand_count: int, country_count: int):
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("#### 🚗 총 수출량")
        st.metric(label="", value=f"{total_export:,} 대")
    with col5:
        st.markdown("#### 🏢 브랜드 수")
        st.metric(label="", value=brand_count)
    with col6:
        st.markdown("#### 🌍 수출 국가 수")
        st.metric(label="", value=country_count)
