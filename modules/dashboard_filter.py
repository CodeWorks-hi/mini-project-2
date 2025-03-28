# modules/dashboard_filter.py
import streamlit as st

from modules.dashboard_kpi import calculate_kpis, render_kpi_card

def render_filter_options(df):
    st.markdown("""
        <div style='padding: 10px; background-color: #f0f7ec; border-radius: 10px; margin-bottom: 15px;'>
            <h4>필터 및 주요 지표</h4>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        years = sorted({col.split("-")[0] for col in df.columns if "-" in col and col[:4].isdigit()})
        years = [int(y) for y in years]
        year = st.selectbox("연도", years, index=years.index(2023), key="export_year")
    with col2:
        company = st.selectbox("기업명", ["전체", "기아", "현대"], key="export_company")
    st.markdown("---")
    month_cols = [col for col in df.columns if str(year) in col and "-" in col]

    df_filtered = df.copy()
    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == company]

    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)
    kpi1, kpi2 = calculate_kpis(df_filtered, month_cols, brand=company)
    render_kpi_card(kpi1, kpi2)
    st.markdown("---")

    st.markdown("""</div>""", unsafe_allow_html=True)

    return year, company