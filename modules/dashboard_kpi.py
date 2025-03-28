# modules/dashboard_kpi.py
# ----------------------------
# 대시보드 KPI 카드 렌더링 모듈
# - 핵심 성과 지표 시각화
# - 동적 스타일링 및 인터랙티브 요소
# ----------------------------

import streamlit as st
import pandas as pd

def calculate_kpis(df: pd.DataFrame, month_cols: list, brand: str = "전체"):
    df_filtered = df.copy()

    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]

    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    total_export = int(df_filtered[month_cols].sum().sum())
    brand_count = df_filtered["브랜드"].nunique()

    # ✅ 모든 month 값이 0 또는 NaN인 행 제거
    active_export_df = df_filtered[df_filtered[month_cols].fillna(0).sum(axis=1) > 0]
    country_count = active_export_df["지역명"].nunique()

    return total_export, brand_count, country_count

def render_kpi_card(total_export: int, brand_count: int, country_count: int):
    col4, col5 = st.columns(2)
    with col4:
        st.markdown("#### 🚗 총 수출량")
        st.metric(label="", value=f"{total_export:,} 대")
    with col5:
        st.markdown("#### 🌍 수출 지역/국가 수")
        st.metric(label="", value=country_count)
