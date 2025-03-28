# modules/dashboard_filter.py
import streamlit as st

from modules.dashboard_kpi import calculate_kpis_by_car, calculate_kpis_by_plant, calculate_kpis_by_region, render_kpi_card

def render_filter_options(df_region, df_car, df_plant):
    st.markdown("""
        <div style='padding: 10px; background-color: #f0f7ec; border-radius: 10px; margin-bottom: 15px;'>
            <h4>필터 및 주요 지표</h4>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        years = sorted({col.split("-")[0] for col in df_region.columns if "-" in col and col[:4].isdigit()})
        years = [int(y) for y in years]
        year = st.selectbox("연도", years, index=years.index(2023), key="export_year")
    with col2:
        company = st.selectbox("기업명", ["전체", "기아", "현대"], key="export_company")
    st.markdown("---")
    month_cols = [col for col in df_region.columns if str(year) in col and "-" in col]

    new_df_region = df_region.copy()
    new_df_region["총수출"] = new_df_region[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        new_df_region = new_df_region[new_df_region["브랜드"] == company]
    new_df_region["총수출"] = new_df_region[month_cols].sum(axis=1, numeric_only=True)
    kpi_total_export, kpi_export_country = calculate_kpis_by_region(new_df_region, month_cols, brand=company)

    new_df_car = df_car.copy()
    kpi_car_count = calculate_kpis_by_car(new_df_car, month_cols, brand=company)

    new_df_plant = df_plant.copy()
    kpi_plant_count = calculate_kpis_by_plant(new_df_plant, month_cols, brand=company)

    render_kpi_card(kpi_total_export, kpi_export_country, kpi_car_count, kpi_plant_count)
    st.markdown("---")

    st.markdown("""</div>""", unsafe_allow_html=True)

    return year, company