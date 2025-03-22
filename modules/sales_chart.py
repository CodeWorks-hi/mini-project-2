import streamlit as st
import pandas as pd

def show_sales_charts(df: pd.DataFrame):
    st.subheader("📊 판매 현황 차트")

    df["판매일"] = pd.to_datetime(df["판매일"], errors="coerce")
    df["연월"] = df["판매일"].dt.to_period("M").astype(str)

    monthly_sales = df.groupby("연월")["수량"].sum().reset_index()
    type_sales = df.groupby("차종")["수량"].sum().sort_values(ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(monthly_sales.set_index("연월"))
    with col2:
        st.bar_chart(type_sales)
