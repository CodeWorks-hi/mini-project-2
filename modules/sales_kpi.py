# modules/sales_kpi.py

import streamlit as st
import pandas as pd
import pydeck as pdk

import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

def show_kpi_cards(df: pd.DataFrame):
    """판매 요약용 KPI 카드 출력 함수"""
    try:
        if df.empty:
            st.warning("데이터가 없습니다.")
            return

        total_sales = int(df["수량"].sum())
        total_revenue = int(df["가격"].sum()) if "가격" in df.columns else 0
        model_count = df["차종"].nunique() if "차종" in df.columns else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 판매량", f"{total_sales:,} 대")
        col2.metric("총 매출", f"₩{total_revenue:,}")
        col3.metric("판매 차종 수", f"{model_count} 종")

    except Exception as e:
        st.error(f"KPI 생성 오류: {str(e)}")

def render_kpi_cards(kpi1: int, kpi2: int, kpi3: int):
    """KPI 카드 렌더링 함수"""
    col1, col2, col3 = st.columns(3)
    col1.metric("총 수출량", f"{kpi1:,} 대")
    col2.metric("브랜드 수", f"{kpi2} 개")
    col3.metric("진출 국가", f"{kpi3} 개")

def render_top_bottom_countries(data: pd.DataFrame):
    """상위/하위 수출국 표시"""
    st.subheader("🌍 수출 상위/하위 국가")
    col1, col2 = st.columns(2)
    top5 = data.nlargest(5, '총수출')
    bottom5 = data.nsmallest(5, '총수출')

    with col1:
        st.markdown("##### 🏆 상위 5개국")
        st.dataframe(top5[['지역명', '총수출']], hide_index=True)
    with col2:
        st.markdown("##### 📉 하위 5개국")
        st.dataframe(bottom5[['지역명', '총수출']], hide_index=True)

def render_map(data: pd.DataFrame):
    """지도 시각화"""
    return pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=20,
            longitude=0,
            zoom=1.3,
            pitch=40.5,
            bearing=-27.36
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=data,
                get_position='[경도, 위도]',
                get_radius='총수출 / 0.5',
                get_fill_color='[200, 30, 0, 160]',
                pickable=True
            )
        ],
        tooltip={
            "html": "<b>지역명:</b> {지역명}<br><b>차량:</b> {차량 구분}<br><b>수출량:</b> {총수출} 대",
            "style": {"backgroundColor": "#2a3f5f", "color": "white"}
        }
    )

def render_factory_chart(prod_df: pd.DataFrame, selected_year: int):
    """공장별 생산량 시각화"""
    st.subheader("🏭 공장별 생산량 비교")
    try:
        yearly = prod_df[prod_df["연도"] == selected_year]
        if yearly.empty:
            st.warning(f"{selected_year}년 데이터가 없습니다.")
            return
        factory_grouped = yearly.groupby(["브랜드", "공장명(국가)"]).sum(numeric_only=True)
        factory_grouped["총생산"] = factory_grouped.sum(axis=1)
        factory_grouped = factory_grouped.reset_index()

        chart = alt.Chart(factory_grouped).mark_bar().encode(
            x=alt.X("총생산:Q", title="총 생산량"),
            y=alt.Y("공장명(국가):N", sort='-x', title="공장명"),
            color="브랜드:N",
            tooltip=["브랜드", "공장명(국가)", alt.Tooltip("총생산", format=",")]
        ).properties(height=400)

        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"생산량 차트 생성 오류: {str(e)}")

