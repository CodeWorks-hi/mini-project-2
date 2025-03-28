# modules/dashboard_filter.py
import streamlit as st

def render_filter_options(df):
    st.markdown("""
        <div style='padding: 10px; background-color: #f0f7ec; border-radius: 10px; margin-bottom: 15px;'>
            <h4>🎯 필터 및 주요 지표</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        years = sorted({col.split("-")[0] for col in df.columns if "-" in col and col[:4].isdigit()})
        years = [int(y) for y in years]
        year = st.selectbox("연도", years, index=years.index(2023), key="export_year")

    with col2:
        company = st.selectbox("기업명", ["전체", "기아", "현대"], key="export_company")

    st.markdown("""</div>""", unsafe_allow_html=True)

    return year, company