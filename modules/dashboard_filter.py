# modules/dashboard_filter.py
# ----------------------------
# 대시보드 전용 필터 UI 및 필터링 함수 모듈
# ----------------------------

import streamlit as st
import pandas as pd

def render_dashboard_filters(df):
    """
    대시보드 상단 필터 영역 구성
    - 연도, 브랜드, 지역, 차종
    """
    st.subheader("📌 데이터 필터")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year_options = sorted(df["연도"].dropna().unique(), reverse=True)
        selected_year = st.selectbox("연도 선택", year_options, key="filter_year")

    with col2:
        brand_options = sorted(df["브랜드"].dropna().unique())
        selected_brand = st.selectbox("브랜드 선택", ["전체"] + brand_options, key="filter_brand")

    with col3:
        region_options = sorted(df["지역"].dropna().unique()) if "지역" in df.columns else []
        selected_region = st.selectbox("지역 선택", ["전체"] + region_options, key="filter_region")

    with col4:
        car_type_options = sorted(df["차종"].dropna().unique()) if "차종" in df.columns else []
        selected_type = st.selectbox("차종 선택", ["전체"] + car_type_options, key="filter_type")

    return selected_year, selected_brand, selected_region, selected_type

def apply_filters(df, year, brand, region, car_type):
    """
    선택된 필터를 기반으로 데이터 필터링
    """
    df_filtered = df[df["연도"] == year]

    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]

    if region != "전체" and "지역" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["지역"] == region]

    if car_type != "전체" and "차종" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["차종"] == car_type]

    return df_filtered.reset_index(drop=True)
