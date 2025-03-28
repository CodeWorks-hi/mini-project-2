# modules/dashboard_kpi.py
# ----------------------------
# 대시보드 KPI 카드 렌더링 모듈
# - 핵심 성과 지표 시각화
# - 동적 스타일링 및 인터랙티브 요소
# ----------------------------

import streamlit as st
import pandas as pd

def calculate_kpis_by_region(df_region: pd.DataFrame, month_cols: list, all_month_cols: list, brand: str, year: int):
    if brand != "전체":
        df_region = df_region[df_region["브랜드"] == brand]

    # 총 수출량
    df_region["총수출"] = df_region[month_cols].sum(axis=1, numeric_only=True)
    total_export = int(df_region[month_cols].sum().sum())

    # 수출 지역/국가 수
    active_export_df = df_region[df_region[month_cols].fillna(0).sum(axis=1) > 0]
    region_count = active_export_df["지역명"].nunique()

    # 전년 대비 수출 증가율
    current_year = [col for col in all_month_cols if col.startswith(str(year))]
    last_year = [col for col in all_month_cols if col.startswith(str(year - 1))]
    if year == 2016:
        export_growth = "-"
    else:
        current_sum = df_region[current_year].sum().sum()
        last_sum = df_region[last_year].sum().sum()
        ratio = (((current_sum - last_sum) / last_sum) * 100).round(2)
        export_growth = f"{ratio}%" if last_sum > 0 else None

    # 최다 수출 국가
    top_region = df_region.loc[df_region["총수출"].idxmax(), "지역명"]


    return total_export, region_count, export_growth, top_region


def calculate_kpis_by_plant(df_plant: pd.DataFrame, month_cols: list, all_month_cols: list, brand: str, year: int):
    if brand != "전체":
        df_plant = df_plant[df_plant["브랜드"] == brand]

    # 총 생산량
    df_plant["총생산"] = df_plant[month_cols].sum(axis=1, numeric_only=True)
    total_prods = int(df_plant[month_cols].sum().sum())

    # 생산 공장 수
    df_temp = df_plant[df_plant["총생산"] > 0]
    plant_count = df_temp["공장명(국가)"].nunique()

    # 전년 대비 생산 증가율
    current_year = [col for col in all_month_cols if col.startswith(str(year))]
    last_year = [col for col in all_month_cols if col.startswith(str(year - 1))]
    if year == 2016:
        prods_growth = "-"
    else:
        current_sum = df_plant[current_year].sum().sum()
        last_sum = df_plant[last_year].sum().sum()
        ratio = (((current_sum - last_sum) / last_sum) * 100).round(2)
        prods_growth = f"{ratio}%" if last_sum > 0 else None

    # 최다 생산 공장
    top_plant = df_plant.loc[df_plant["총생산"].idxmax(), "공장명(국가)"]


    return total_prods, plant_count, prods_growth, top_plant


def calculate_kpis_by_car(df_car: pd.DataFrame, month_cols: list, all_month_cols: list, brand: str, year: int):
    if brand != "전체":
        df_car = df_car[df_car["브랜드"] == brand]
    
    # 총 판매량
    df_car["총판매"] = df_car[month_cols].sum(axis=1, numeric_only=True)
    total_sales = int(df_car[month_cols].sum().sum())

    # 판매 차종 수
    df_car["월별합"] = df_car[month_cols].sum(axis=1, numeric_only=True)
    car_count = (df_car["월별합"] > 0).sum()

    # 전년 대비 판매 증가율
    current_year = [col for col in all_month_cols if col.startswith(str(year))]
    last_year = [col for col in all_month_cols if col.startswith(str(year - 1))]
    if year == 2016:
        sales_growth = "-"
    else:
        current_sum = df_car[current_year].sum().sum()
        last_sum = df_car[last_year].sum().sum()
        ratio = (((current_sum - last_sum) / last_sum) * 100).round(2)
        sales_growth = f"{ratio}%" if last_sum > 0 else None
    
    # 최다 판매 차종
    top_car = df_car.loc[df_car["총판매"].idxmax(), "차종"]


    return total_sales, car_count, sales_growth, top_car


def export_render_kpi_card(total_export: int, region_count: int, export_growth: int, top_region: str):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 🚗 총 수출량")
        st.metric(label="", value=f"{total_export:,} 대")
    with col2:
        st.markdown("#### 🌍 수출 지역/국가 수")
        st.metric(label="", value=region_count)
    with col3:
        st.markdown("#### 🌍 전년 대비 수출 증가율")
        st.metric(label="", value=export_growth)
    with col4:
        st.markdown("#### 🌍 최대 수출 대상국")
        st.metric(label="", value=top_region)


def prods_render_kpi_card(total_prods: int, plant_count: int, prods_growth: int, top_plant: str):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 🚗 총 생산량")
        st.metric(label="", value=f"{total_prods:,} 대")
    with col2:
        st.markdown("#### 총 생산 공장 수")
        st.metric(label="", value=plant_count)
    with col3:
        st.markdown("#### 🌍 전년 대비 생산 증가율")
        st.metric(label="", value=prods_growth)
    with col4:
        st.markdown("#### 🌍 최대 생산 공장")
        st.metric(label="", value=top_plant)


def sales_render_kpi_card(total_sales: int, car_count: int, sales_growth: int, top_car: int):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 🚗 총 판매량")
        st.metric(label="", value=f"{total_sales:,} 대")
    with col2:
        st.markdown("#### 🌍 판매 차종 수")
        st.metric(label="", value=car_count)
    with col3:
        st.markdown("#### 🌍 전년 대비 판매 증가율")
        st.metric(label="", value=sales_growth)
    with col4:
        st.markdown("#### 🌍 최다 판매 차종")
        st.metric(label="", value=top_car)