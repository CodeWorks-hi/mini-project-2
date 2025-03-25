# modules/dashboard_insight.py
# ----------------------------
# 대시보드 인사이트 생성 모듈
# - 자동화된 데이터 분석
# - 동적 인사이트 생성
# ----------------------------

import streamlit as st
import pandas as pd
from typing import Tuple, Optional
from datetime import datetime

def generate_sales_insights(df: pd.DataFrame, month_cols: list) -> Tuple[str, str, float]:
    """판매 데이터 분석을 위한 핵심 인사이트 생성"""
    try:
        if df.empty or '차종' not in df.columns:
            return "-", "-", 0.0

        # 월별 총 판매량 계산
        sales_by_model = df.groupby('차종')[month_cols].sum().sum(axis=1)
        
        # 상위 판매 차종
        top_models = sales_by_model.nlargest(3)
        top_model = " 🥇 ".join(top_models.index.tolist())
        
        # 최저 판매 차종
        bottom_models = sales_by_model.nsmallest(3)
        bottom_model = " 🥈 ".join(bottom_models.index.tolist())
        
        # 평균 대비 판매 비율
        avg_sales = sales_by_model.mean()
        
        return top_model, bottom_model, avg_sales

    except Exception as e:
        st.error(f"판매 인사이트 생성 오류: {str(e)}")
        return "-", "-", 0.0

def generate_inventory_insights(df: pd.DataFrame) -> Tuple[str, str, float]:
    """재고 데이터 분석을 위한 핵심 인사이트 생성"""
    try:
        if df.empty or '차종' not in df.columns or '예상재고' not in df.columns:
            return "-", "-", 0.0

        # 재고 분석
        overstock = df[df['예상재고'] > df['예상재고'].quantile(0.75)]
        understock = df[df['예상재고'] < df['예상재고'].quantile(0.25)]
        
        # 상위 재고 차종
        top_stock = overstock.nlargest(3, '예상재고')['차종'].tolist()
        top_stock_str = " 🏭 ".join(top_stock) if top_stock else "-"
        
        # 부족 재고 차종
        low_stock = understock.nsmallest(3, '예상재고')['차종'].tolist()
        low_stock_str = " ⚠️ ".join(low_stock) if low_stock else "-"
        
        # 전체 재고량
        total_stock = df['예상재고'].sum()
        
        return top_stock_str, low_stock_str, total_stock

    except Exception as e:
        st.error(f"재고 인사이트 생성 오류: {str(e)}")
        return "-", "-", 0.0

def show_insight(sales_df: pd.DataFrame, inventory_df: pd.DataFrame, month_cols: list) -> None:
    """
    종합 인사이트 대시보드 생성
    
    Args:
        sales_df (pd.DataFrame): 월별 판매 데이터
        inventory_df (pd.DataFrame): 재고 데이터
        month_cols (list): 월별 컬럼 리스트
    """
    st.subheader(f"🔍 {datetime.now().month}월 주요 인사이트")
    
    # 판매 인사이트
    top_model, bottom_model, avg_sales = generate_sales_insights(sales_df, month_cols)
    
    # 재고 인사이트
    top_stock, low_stock, total_stock = generate_inventory_insights(inventory_df)
    
    # 인사이트 카드 레이아웃
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 🚗 판매 현황")
            if top_model != "-":
                st.success(f"**BEST 3 차종**: {top_model}")
                st.metric("월 평균 판매량", f"{avg_sales:,.0f}대")
            if bottom_model != "-":
                st.error(f"**개선 필요 차종**: {bottom_model}")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📦 재고 현황")
            if top_stock != "-":
                st.warning(f"**과잉 재고 차종**: {top_stock}")
            if low_stock != "-":
                st.info(f"**재고 부족 차종**: {low_stock}")
            st.metric("총 예상 재고량", f"{total_stock:,.0f}대")

    # 추가 분석 섹션
    with st.expander("📈 심화 분석 보기"):
        tab1, tab2 = st.tabs(["판매 분포", "재고 트렌드"])
        
        with tab1:
            if not sales_df.empty:
                st.altair_chart(create_sales_distribution_chart(sales_df, month_cols))
        
        with tab2:
            if not inventory_df.empty:
                st.altair_chart(create_inventory_trend_chart(inventory_df))

def create_sales_distribution_chart(df: pd.DataFrame, month_cols: list):
    """Altair를 이용한 판매 분포 시각화"""
    # ... (차트 생성 로직 구현) ...

def create_inventory_trend_chart(df: pd.DataFrame):
    """Altair를 이용한 재고 트렌드 시각화"""
    # ... (차트 생성 로직 구현) ...
