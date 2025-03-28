# modules/dashboard_kpi.py
# ----------------------------
# 대시보드 KPI 카드 렌더링 모듈
# - 핵심 성과 지표 시각화
# - 동적 스타일링 및 인터랙티브 요소
# ----------------------------

import streamlit as st
import pandas as pd

def calculate_kpis_by_region(df: pd.DataFrame, month_cols: list, brand: str = "전체"):
    df_filtered = df.copy()

    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]

    # 총 수출량
    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    total_export = int(df_filtered[month_cols].sum().sum())

    # 수출 지역/국가 수
    active_export_df = df_filtered[df_filtered[month_cols].fillna(0).sum(axis=1) > 0]
    country_count = active_export_df["지역명"].nunique()

    return total_export, country_count


def calculate_kpis_by_car(df: pd.DataFrame, month_cols: list, brand: str = "전체"):
    df_filtered = df.copy()

    # 브랜드 필터링
    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]

    if not month_cols or not all(col in df.columns for col in month_cols):
        st.warning("유효한 월별 컬럼이 존재하지 않습니다.")
        return
    
    df_filtered["월별합"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    car_count = (df_filtered["월별합"] > 0).sum()

    return car_count


def calculate_kpis_by_plant(df: pd.DataFrame, month_cols: list, brand: str = "전체"):
    df_filtered = df.copy()

    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]

    if not month_cols or not all(col in df.columns for col in month_cols):
        st.warning("유효한 월별 컬럼이 존재하지 않습니다.")
        return

    df_filtered["합계"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    df_filtered = df_filtered[df_filtered["합계"] > 0]

    plant_count = df_filtered["공장명(국가)"].nunique()

    return plant_count


def render_kpi_card(total_export: int, country_count: int, car_count: int, plant_count: int):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 🚗 총 수출량")
        st.metric(label="", value=f"{total_export:,} 대")
    with col2:
        st.markdown("#### 🌍 수출 지역/국가 수")
        st.metric(label="", value=country_count)
    with col3:
        st.markdown("#### 총 판매 차종 수")
        st.metric(label="", value=car_count)
    with col4:
        st.markdown("#### 총 생산 공장 수")
        st.metric(label="", value=plant_count)
