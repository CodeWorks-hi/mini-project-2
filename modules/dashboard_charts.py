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
import plotly.express as px

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

def render_top_bottom_summary(merged_df: pd.DataFrame, company, year):

    st.markdown(f"""
    <div style='background-color:#ede7f6;padding:20px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,0.05);'>
        <h4>{year}년 {company} 국가별 총 판매량</h4>
    </div>
    """, unsafe_allow_html=True)

    merged_df.drop(columns=["대륙"], inplace=True)
    start_col = f"{year}-01"
    end_col = f"{year}-12"
    merged_df = pd.concat([merged_df.iloc[:, 0], merged_df.loc[:, start_col:end_col]], axis = 1)
    merged_df = merged_df[merged_df.loc[:, start_col:end_col].fillna(0).sum(axis=1) > 0]

    st.dataframe(merged_df, hide_index=True)

    # 총수출 시각화용 컬럼 생성
    merged_df["총수출"] = merged_df.loc[:, start_col:end_col].sum(axis=1)

    st.markdown("""
    <div style='margin-top:20px; padding:10px; background-color:#fff3e0; border-radius:10px;'>
        <h5 style='margin-bottom:10px;'>🚚 국가별 총 판매량 시각화</h5>
    </div>
    """, unsafe_allow_html=True)
    total_export_df = merged_df[["지역명", "총수출"]].sort_values("총수출", ascending=False)
    fig_total = px.bar(total_export_df, x="지역명", y="총수출", color="지역명",
                       labels={"총수출": "총수출", "지역명": "국가"},
                       height=400)
    st.plotly_chart(fig_total, use_container_width=True)

    monthly_data = []

    for month in pd.date_range(start=start_col, end=end_col, freq='MS').strftime('%Y-%m'):
        if month in merged_df.columns:
            month_data = merged_df[["지역명", month]].copy()
            month_data = month_data.dropna()
            month_data = month_data[month_data[month] > 0]
            month_data["월"] = month
            month_data.rename(columns={month: "수출량"}, inplace=True)
            monthly_data.append(month_data)

    monthly_df = pd.concat(monthly_data).reset_index(drop=True)

    # 월별 국가별 수출량 집계
    grouped_monthly = (
        monthly_df.groupby(["월", "지역명"], as_index=False)["수출량"]
        .sum()
        .sort_values(["월", "수출량"], ascending=[True, False])
    )

    # Top 3
    grouped_monthly["순위_top"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=False).astype(int)
    top_df = grouped_monthly[grouped_monthly["순위_top"] <= 3].sort_values(["월", "순위_top"])

    # Bottom 3
    grouped_monthly["순위_bottom"] = grouped_monthly.groupby("월")["수출량"].rank(method="first", ascending=True).astype(int)
    bottom_df = grouped_monthly[grouped_monthly["순위_bottom"] <= 3].sort_values(["월", "순위_bottom"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#f3e5f5; border-radius:10px;'>
            <h5 style='margin-bottom:10px;'>📈 월별 Top 3 수출 국가</h5>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(top_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    with col2:
        st.markdown("""
        <div style='margin-top:20px; padding:10px; background-color:#e0f7fa; border-radius:10px;'>
            <h5 style='margin-bottom:10px;'>📉 월별 Bottom 3 수출 국가</h5>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(bottom_df.style.format({'수출량': '{:,}'}), use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top:20px; padding:10px; background-color:#ede7f6; border-radius:10px;'>
        <h5 style='margin-bottom:10px;'>📊 월별 Top 3 수출 국가 시각화</h5>
    </div>
    """, unsafe_allow_html=True)
    fig_top = px.bar(top_df, x="월", y="수출량", color="지역명", barmode="group",
                     labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                     height=400)
    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("""
    <div style='margin-top:20px; padding:10px; background-color:#f0f4c3; border-radius:10px;'>
        <h5 style='margin-bottom:10px;'>📊 월별 Bottom 3 수출 국가 시각화</h5>
    </div>
    """, unsafe_allow_html=True)
    fig_bottom = px.bar(bottom_df, x="월", y="수출량", color="지역명", barmode="group",
                        labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
                        height=400)
    st.plotly_chart(fig_bottom, use_container_width=True)

    # 📈 월별 국가별 판매량 변화 추이 (라인 차트)
    st.markdown("""
    <div style='margin-top:30px; padding:10px; background-color:#e3f2fd; border-radius:10px;'>
        <h5 style='margin-bottom:10px;'>📈 월별 국가별 판매량 변화 추이</h5>
    </div>
    """, unsafe_allow_html=True)

    # 월별 컬럼만 추출
    month_cols = pd.date_range(start=start_col, end=end_col, freq='MS').strftime('%Y-%m')

    # melt 전에 국가별로 월별 합계 집계
    aggregated = merged_df.groupby("지역명")[month_cols].sum().reset_index()

    # 그 후 melt
    line_df = aggregated.melt(
        id_vars="지역명",
        value_vars=month_cols,
        var_name="월", value_name="수출량"
    )
    line_df = line_df.dropna()
    line_df = line_df[line_df["수출량"] > 0]

    fig_line = px.line(
        line_df,
        x="월", y="수출량", color="지역명",
        labels={"수출량": "수출량", "월": "월", "지역명": "국가"},
        markers=True,
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)
