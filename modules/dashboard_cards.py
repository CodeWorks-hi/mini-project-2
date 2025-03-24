# modules/dashboard_cards.py
# ----------------------------
# KPI 카드 시각화 컴포넌트
# - 생산, 판매, 수출, 재고 요약 정보
# ----------------------------

import streamlit as st

def show_kpi_cards(prod_df, sales_df, export_df, month_cols):
    total_prod = int(prod_df[month_cols].sum().sum())
    total_sales = int(sales_df[month_cols].sum().sum())
    total_export = int(export_df[month_cols].sum().sum())
    total_stock = total_prod - total_sales

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏭 총 생산량", f"{total_prod:,} 대")
    col2.metric("🛒 총 판매량", f"{total_sales:,} 대")
    col3.metric("🚢 총 수출량", f"{total_export:,} 대")
    col4.metric("📦 예상 재고량", f"{total_stock:,} 대")

    return total_prod, total_sales, total_export, total_stock
