# modules/dashboard_kpi.py
# ----------------------------
# 대시보드 KPI 카드 렌더링 모듈
# - 핵심 성과 지표 시각화
# - 동적 스타일링 및 인터랙티브 요소
# ----------------------------

import streamlit as st
import pandas as pd
from typing import Dict, Any

def calculate_kpis(df: pd.DataFrame, month_cols: list) -> Dict[str, Any]:
    """
    KPI 계산 함수
    
    Args:
        df (pd.DataFrame): 분석 대상 데이터프레임
        month_cols (list): 월별 컬럼 리스트
    
    Returns:
        Dict[str, Any]: 계산된 KPI 값들
    """
    total_export = int(df[month_cols].sum().sum())
    brand_count = df["브랜드"].nunique()
    country_count = df["지역명"].nunique()
    
    # 추가 KPI 계산
    avg_monthly_export = total_export / len(month_cols)
    top_brand = df.groupby("브랜드")[month_cols].sum().sum(axis=1).idxmax()
    top_country = df.groupby("지역명")[month_cols].sum().sum(axis=1).idxmax()
    
    return {
        "total_export": total_export,
        "brand_count": brand_count,
        "country_count": country_count,
        "avg_monthly_export": avg_monthly_export,
        "top_brand": top_brand,
        "top_country": top_country
    }

def render_kpi_cards(kpis: Dict[str, Any], prev_kpis: Dict[str, Any] = None):
    """
    KPI 카드 렌더링 함수
    
    Args:
        kpis (Dict[str, Any]): 현재 KPI 값들
        prev_kpis (Dict[str, Any], optional): 이전 기간 KPI 값들 (비교용)
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.metric(
                "총 수출량",
                f"{kpis['total_export']:,} 대",
                delta=f"{kpis['total_export'] - prev_kpis['total_export']:,} 대" if prev_kpis else None,
                delta_color="normal"
            )
            st.caption(f"월 평균: {kpis['avg_monthly_export']:,.0f} 대")
    
    with col2:
        with st.container(border=True):
            st.metric(
                "브랜드 수",
                kpis['brand_count'],
                delta=kpis['brand_count'] - prev_kpis['brand_count'] if prev_kpis else None
            )
            st.caption(f"최고 브랜드: {kpis['top_brand']}")
    
    with col3:
        with st.container(border=True):
            st.metric(
                "수출 국가 수",
                kpis['country_count'],
                delta=kpis['country_count'] - prev_kpis['country_count'] if prev_kpis else None
            )
            st.caption(f"최대 수출국: {kpis['top_country']}")
    
    # 추가 KPI 섹션
    with st.expander("🔍 상세 KPI 보기"):
        col4, col5 = st.columns(2)
        with col4:
            st.info(f"🏆 최고 수출 브랜드: **{kpis['top_brand']}**")
        with col5:
            st.success(f"🌎 최대 수출 국가: **{kpis['top_country']}**")

def render_kpi_trend(df: pd.DataFrame, month_cols: list):
    """
    KPI 트렌드 차트 렌더링 함수
    
    Args:
        df (pd.DataFrame): 분석 대상 데이터프레임
        month_cols (list): 월별 컬럼 리스트
    """
    st.subheader("📈 KPI 트렌드")
    
    # 월별 총 수출량 계산
    monthly_export = df[month_cols].sum()
    
    # 라인 차트 생성
    st.line_chart(monthly_export)


