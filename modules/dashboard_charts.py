# modules/dashboard_charts.py
# ----------------------------
# 대시보드용 주요 차트 시각화 모듈
# - 월별 생산/판매/수출 추이 시각화
# - 재고 상태 분석 및 경고 시스템
# - 공장별 생산량 비교 차트
# ----------------------------

import altair as alt
import pydeck as pdk
import streamlit as st
import pandas as pd

# 현대 도넛 차트

def render_hyundai_chart(year: int):
    st.markdown("""
    <div style='background-color:#f3f4f6;padding:20px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,0.05);'>
    <h4>현대 공장별 생산 비중</h4>
    """, unsafe_allow_html=True)

    df = pd.read_csv("data/processed/hyundai-by-plant.csv")
    df["브랜드"] = "현대"
    df = df.loc[df["공장명(국가)"] != "CKD (모듈형 조립 방식)", :]

    month_cols = [col for col in df.columns if str(year) in col and "-" in col]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")

    grouped = df.groupby("공장명(국가)")[month_cols].sum(numeric_only=True).reset_index()
    grouped["총생산"] = grouped[month_cols].sum(axis=1)

    if grouped.empty:
        st.warning(f"{year}년 현대 생산 데이터가 없습니다.")
    else:
        chart = alt.Chart(grouped).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="총생산", type="quantitative"),
            color=alt.Color(field="공장명(국가)", type="nominal", legend=alt.Legend(title="공장")),
            tooltip=["공장명(국가)", "총생산"]
        ).properties(
            width=400,
            height=400,
            title=f"{year}년 현대 공장별 생산 비중"
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# 기아 도넛 차트
def render_kia_chart(year: int):
    st.markdown("""
    <div style='background-color:#fff8e1;padding:20px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,0.05);'>
    <h4>기아 공장별 생산 비중</h4>
    """, unsafe_allow_html=True)

    df = pd.read_csv("data/processed/kia-by-plant.csv")
    df["브랜드"] = "기아"

    month_cols = [col for col in df.columns if str(year) in col and "-" in col]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")

    grouped = df.groupby("공장명(국가)")[month_cols].sum(numeric_only=True).reset_index()
    grouped["총생산"] = grouped[month_cols].sum(axis=1)

    if grouped.empty:
        st.warning(f"{year}년 기아 생산 데이터가 없습니다.")
    else:
        chart = alt.Chart(grouped).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="총생산", type="quantitative"),
            color=alt.Color(field="공장명(국가)", type="nominal", legend=alt.Legend(title="공장")),
            tooltip=["공장명(국가)", "총생산"]
        ).properties(
            width=400,
            height=400,
            title=f"{year}년 기아 공장별 생산 비중"
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# 지도 시각화
def render_export_map(merged_df: pd.DataFrame, vehicle_type: str, color_map: dict):
    st.markdown("""
    <div style='background-color:#f9fbe7;padding:15px;border-radius:12px;margin-bottom:20px;'>
    <h4>🗺️ 수출 국가별 지도</h4>
    """, unsafe_allow_html=True)

    if len(merged_df) == 0:
        st.warning("표시할 지도 데이터가 없습니다. 필터를 바꿔보세요.")
    else:
        color = color_map.get(vehicle_type, [173, 216, 230, 160])  # 기본색: 연하늘
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1.3),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=merged_df,
                    get_position='[경도, 위도]',
                    get_radius='총수출 / 0.5',
                    get_fill_color=f"[{color[0]}, {color[1]}, {color[2]}, 160]",
                    pickable=True
                )
            ],
            tooltip={"text": "{지역명}\n차량: {차량 구분}\n수출량: {총수출} 대"}
        ))

    st.markdown("</div>", unsafe_allow_html=True)


def render_top_bottom_summary(merged_df: pd.DataFrame):

    st.markdown("""
    <div style='background-color:#ede7f6;padding:15px;border-radius:12px;margin-bottom:20px;'>
    <h5>📦 수출 상하위 국가 요약</h5>
    """, unsafe_allow_html=True)

    st.dataframe(merged_df)

    top_table = merged_df.sort_values("총수출", ascending=False).head(3)
    bottom_table = merged_df.sort_values("총수출").head(3)

    top_display = top_table[["지역명", "총수출"]].reset_index(drop=True)
    bottom_display = bottom_table[["지역명", "총수출"]].reset_index(drop=True)

    st.dataframe(top_display.style.format({'총수출': '{:,}'}), use_container_width=True, hide_index=True)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    st.dataframe(bottom_display.style.format({'총수출': '{:,}'}), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
