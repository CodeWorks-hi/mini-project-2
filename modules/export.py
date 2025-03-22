# modules/export.py
# ----------------------------
# 수출 관리 모듈
# - 국가별/지역별 수출 실적 관리
# - 수출 일정 및 국가 정책 분석 기반 확장 가능
# ----------------------------

import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

def export_ui():
    st.title("📤 수출 실적 대시보드")
    st.button("+ 수출 등록")

    # 데이터 로딩
    hyundai = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    kia = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"
    df = pd.concat([hyundai, kia], ignore_index=True)

    month_cols = [f"{i}월" for i in range(1, 13)]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce')

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 기본 현황", "🌍 국가별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 수출 지도", "📊 성장률 분석"
    ])

    # --- 기본 현황 ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique())
        with col2:
            year = st.selectbox("연도 선택", sorted(df["연도"].dropna().unique(), reverse=True))
        with col3:
            country_list = df[df["브랜드"] == brand]["국가명"].dropna().unique()
            country = st.selectbox("국가 선택", country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"])

        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["국가명"] == country)]

        if not filtered.empty:
            total_export = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
            avg_export = int(filtered[month_cols].mean(numeric_only=True).mean(skipna=True))
            type_count = filtered["차량 구분"].nunique()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("총 수출량", f"{total_export:,} 대")
            kpi2.metric("평균 수출량", f"{avg_export:,} 대")
            kpi3.metric("차량 구분 수", f"{type_count} 종")

            df_melted = filtered.melt(id_vars=["차량 구분"], value_vars=month_cols, var_name="월", value_name="수출량")
            df_melted.dropna(subset=["수출량"], inplace=True)

            if not df_melted.empty:
                chart = alt.Chart(df_melted).mark_line(point=True).encode(
                    x="월",
                    y="수출량",
                    color="차량 구분"
                ).properties(width=900, height=400, title="📈 월별 차량 구분 수출 추이")
                st.altair_chart(chart, use_container_width=True)

            with st.expander("📋 원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)

            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 현재 데이터 다운로드", data=csv, file_name=f"{brand}_{country}_{year}_수출실적.csv", mime="text/csv")
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # --- 국가별 비교 ---
    with tab2:
        brand = st.selectbox("브랜드 선택 (국가 비교)", df["브랜드"].dropna().unique())
        year = st.selectbox("연도 선택 (국가 비교)", sorted(df["연도"].dropna().unique(), reverse=True))
        grouped = df[(df["브랜드"] == brand) & (df["연도"] == year)]
        compare_df = grouped.groupby("국가명")[month_cols].sum(numeric_only=True)
        compare_df["총수출"] = compare_df.sum(axis=1)
        compare_df = compare_df.reset_index()

        chart = alt.Chart(compare_df).mark_bar().encode(
            x=alt.X("총수출:Q", title="총 수출량"),
            y=alt.Y("국가명:N", sort="-x", title="국가명"),
            color="국가명:N"
        ).properties(width=800, height=500, title="🌍 국가별 총 수출량 비교")
        st.altair_chart(chart, use_container_width=True)

    # --- 연도별 추이 ---
    with tab3:
        brand = st.selectbox("브랜드 선택 (연도별 추이)", df["브랜드"].dropna().unique())
        country = st.selectbox("국가 선택 (연도별 추이)", df[df["브랜드"] == brand]["국가명"].dropna().unique())
        yearly = df[(df["브랜드"] == brand) & (df["국가명"] == country)]
        yearly_sum = yearly.groupby("연도")[month_cols].sum(numeric_only=True)
        yearly_sum["총수출"] = yearly_sum.sum(axis=1)
        yearly_sum = yearly_sum.reset_index()

        line_chart = alt.Chart(yearly_sum).mark_line(point=True).encode(
            x="연도:O",
            y="총수출:Q"
        ).properties(title="📈 연도별 총 수출량 변화 추이", width=700, height=400)
        st.altair_chart(line_chart, use_container_width=True)

    # --- 목표 달성률 ---
    with tab4:
        brand = st.selectbox("브랜드 선택 (목표)", df["브랜드"].dropna().unique())
        year = st.selectbox("연도 선택 (목표)", sorted(df["연도"].dropna().unique(), reverse=True))
        country = st.selectbox("국가 선택 (목표)", df[df["브랜드"] == brand]["국가명"].dropna().unique())
        goal = st.number_input("🎯 수출 목표 (대)", min_value=0, step=1000)

        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["국가명"] == country)]
        actual = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True)) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0

        st.metric("총 수출량", f"{actual:,} 대")
        st.metric("목표 달성률", f"{rate:.2f}%")

    # --- 수출 지도 ---
    with tab5:
        st.subheader("🗺️ 국가별 수출량 지도 시각화")
        try:
            location_df = pd.read_csv("data/세일즈파일/국가_위치정보_수출.csv")
            export_sum = df.groupby("국가명")[month_cols].sum(numeric_only=True)
            export_sum["총수출"] = export_sum.sum(axis=1)
            export_sum = export_sum.reset_index()
            merged = pd.merge(location_df, export_sum, on="국가명", how="left")
            merged = merged.dropna(subset=["위도", "경도", "총수출"])

            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=20,
                    longitude=0,
                    zoom=1.5,
                    pitch=30
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=merged,
                        get_position='[경도, 위도]',
                        get_radius='총수출 / 3',
                        get_fill_color='[30, 144, 255, 160]',
                        pickable=True
                    )
                ],
                tooltip={"text": "{국가명}\n총수출: {총수출} 대"}
            ))
        except Exception as e:
            st.error(f"지도 시각화 로딩 중 오류 발생: {e}")
    # --- 성장률 분석 ---
    with tab6:
        st.subheader("📊 국가별 수출 성장률 분석")
        brand = st.selectbox("브랜드 선택 (성장률)", df["브랜드"].dropna().unique())
        year_list = sorted(df["연도"].dropna().unique())

        if len(year_list) < 2:
            st.warning("성장률 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
        else:
            year = st.selectbox("기준 연도 선택", year_list[1:])  # 두 번째 연도부터 선택 가능 (이전 해 있어야 계산 가능)
            prev_year = year_list[year_list.index(year) - 1]

            current = df[(df["브랜드"] == brand) & (df["연도"] == year)]
            previous = df[(df["브랜드"] == brand) & (df["연도"] == prev_year)]

            cur_sum = current.groupby("국가명")[month_cols].sum(numeric_only=True).sum(axis=1).rename("current")
            prev_sum = previous.groupby("국가명")[month_cols].sum(numeric_only=True).sum(axis=1).rename("previous")

            merged = pd.concat([cur_sum, prev_sum], axis=1).dropna()
            merged["성장률"] = ((merged["current"] - merged["previous"]) / merged["previous"] * 100).round(2)
            merged = merged.reset_index()

            top5 = merged.sort_values("성장률", ascending=False).head(5)
            bottom5 = merged.sort_values("성장률").head(5)

            st.markdown(f"#### {prev_year} → {year} 성장률 상위 국가")
            st.dataframe(top5, use_container_width=True)

            st.markdown(f"#### {prev_year} → {year} 성장률 하위 국가")
            st.dataframe(bottom5, use_container_width=True)

            chart = alt.Chart(merged).mark_bar().encode(
                x=alt.X("성장률:Q", title="성장률 (%)"),
                y=alt.Y("국가명:N", sort="-x"),
                color=alt.condition("datum.성장률 > 0", alt.value("#2E8B57"), alt.value("#DC143C"))
            ).properties(
                title=f"📊 {prev_year} → {year} 국가별 수출 성장률",
                width=800,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)


