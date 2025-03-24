# modules/dashboard_insight.py
# ----------------------------
# 인사이트 요약 메시지
# - 가장 많이 팔린 차종, 재고가 가장 많은 차종 등
# ----------------------------

import streamlit as st
import pandas as pd

def show_insight(sales_df, inventory_df, month_cols):
    st.subheader("💡 인사이트 요약")

    # 가장 많이 팔린 차종
    try:
        top_model = sales_df.groupby("차종")[month_cols].sum().sum(axis=1).sort_values(ascending=False).index[0]
    except:
        top_model = "-"

    # 가장 재고가 많은 차종
    try:
        top_stock = inventory_df.sort_values("예상재고", ascending=False).iloc[0]["차종"]
    except:
        top_stock = "-"

    st.info(f"🚗 가장 많이 팔린 차종은 **{top_model}** 입니다.")
    st.info(f"📦 재고가 가장 많이 쌓인 차종은 **{top_stock}** 입니다.")
