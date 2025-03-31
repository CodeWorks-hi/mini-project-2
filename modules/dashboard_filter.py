import streamlit as st

from modules.dashboard_kpi import calculate_kpis_by_car, calculate_kpis_by_plant, calculate_kpis_by_region, export_render_kpi_card, prods_render_kpi_card, sales_render_kpi_card

def render_filter_options(df_region, df_car, df_plant):
    st.markdown("""
        <div style='padding: 10px; background-color: #f0f7ec; border-radius: 10px; margin-bottom: 15px;'>
            <h4>필터 및 주요 지표</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        years = sorted({col.split("-")[0] for col in df_region.columns if "-" in col and col[:4].isdigit()})
        years = [int(y) for y in years]
        year = st.selectbox("연도", years, index=years.index(2024), key="dashboard_year")
    with col2:
        company = st.selectbox("기업명", ["전체", "기아", "현대"], key="dashboard_company")
    with col3:
        data = st.selectbox("데이터 유형", ["수출", "판매", "생산"], key="dashboard_data")
    st.markdown("---")
    all_month_cols = [col for col in df_region.columns if col not in ("지역명", "대륙", "브랜드")]
    month_cols = [col for col in df_region.columns if str(year) in col and "-" in col]
    
    new_df_region = df_region.copy()
    new_df_region["총수출"] = new_df_region[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        new_df_region = new_df_region[new_df_region["브랜드"] == company]
    new_df_region["총수출"] = new_df_region[month_cols].sum(axis=1, numeric_only=True)

    new_df_plant = df_plant.copy()
    new_df_plant["총생산"] = new_df_plant[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        new_df_plant = new_df_plant[new_df_plant["브랜드"] == company]
    new_df_plant["총생산"] = new_df_plant[month_cols].sum(axis=1, numeric_only=True)

    new_df_car = df_car.copy()
    new_df_car["총판매"] = new_df_car[month_cols].sum(axis=1, numeric_only=True)
    if company != "전체":
        new_df_car = new_df_car[new_df_car["브랜드"] == company]
    new_df_car["총판매"] = new_df_car[month_cols].sum(axis=1, numeric_only=True)

    kpi_total_export, kpi_region_count, kpi_export_growth, kpi_top_region = calculate_kpis_by_region(new_df_region, month_cols,
                                                                                                     all_month_cols, company,
                                                                                                     year)
    kpi_total_prods, kpi_plant_count, kpi_prods_growth, kpi_top_plant = calculate_kpis_by_plant(new_df_plant, month_cols,
                                                                                 all_month_cols, company, year)
    kpi_total_sales, kpi_car_count, kpi_sales_growth, kpi_top_car = calculate_kpis_by_car(new_df_car, month_cols,
                                                                                          all_month_cols, company, year)

    if data == "수출":
        export_render_kpi_card(kpi_total_export, kpi_region_count, kpi_export_growth, kpi_top_region)
    elif data == "생산":
        prods_render_kpi_card(kpi_total_prods, kpi_plant_count, kpi_prods_growth, kpi_top_plant)
    elif data == "판매":
        sales_render_kpi_card(kpi_total_sales, kpi_car_count, kpi_sales_growth, kpi_top_car)

    st.markdown("---")

    st.markdown("""</div>""", unsafe_allow_html=True)

    return year, company