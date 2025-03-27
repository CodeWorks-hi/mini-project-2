import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import plotly.graph_objects as go
import re

# 재고 관리
def load_data():
    hyundai = pd.read_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
    kia = pd.read_csv("data/processed/기아_해외공장판매실적_전처리.CSV")

    if "차종" not in hyundai.columns:
        hyundai["차종"] = "기타"
    if "차종" not in kia.columns:
        kia["차종"] = "기타"

    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"
    return pd.concat([hyundai, kia], ignore_index=True)

def goal_achievement_section(df):
    st.title("🎯 목표 달성률")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="brand_select_goal")

    year_options = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True)
    with col2:
        year = st.selectbox("연도 선택", year_options, key="year_select_goal")
    with col3:
        factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(), key="factory_select_goal")
    with col4:
        goal = st.number_input("🎯 생산 목표 (대)", min_value=0, step=1000, key="goal_input")

    month_cols = [col for col in df.columns if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
    filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]

    actual = int(filtered[month_cols].sum().sum()) if not filtered.empty else 0
    rate = (actual / goal * 100) if goal > 0 else 0

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("총 생산량", f"{actual:,} 대")
    with col_b:
        st.metric("목표 달성률", f"{rate:.2f}%")

    fig_donut = go.Figure(data=[go.Pie(
        labels=["실제 생산량", "남은 목표"],
        values=[actual, max(goal - actual, 0)],
        hole=0.5,
        marker_colors=["purple", "lightgray"]
    )])
    fig_donut.update_layout(
        title_text="목표 달성률",
        annotations=[dict(text=f"{rate:.1f}%", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    fig_bar = go.Figure(data=[
        go.Bar(name="목표", x=["목표"], y=[goal], marker_color="lightblue"),
        go.Bar(name="실제 생산량", x=["목표"], y=[actual], marker_color="purple")
    ])
    fig_bar.update_layout(
        barmode="group",
        title="목표 vs 실제 생산량",
        xaxis_title="데이터 유형",
        yaxis_title="수량 (대)",
        legend_title="데이터"
    )

    st.plotly_chart(fig_donut, use_container_width=True)
    st.plotly_chart(fig_bar, use_container_width=True)


def production_ui():
    # ✅ 생산 등록 폼 토글 함수
    def toggle_form():
        st.session_state["show_form"] = not st.session_state.get("show_form", False)

    # ✅ 버튼 라벨 설정
    btn_label = "등록 취소" if st.session_state.get("show_form", False) else "📥 생산 등록"

    # ✅ 버튼 클릭 시 toggle_form 함수 실행
    st.button(btn_label, on_click=toggle_form)

    # ✅ 데이터 로드 (폼 안에서 사용하기 위해 미리 로드)
    df = load_data()

    # ✅ 폼 표시 조건
    if st.session_state.get("show_form", False):
        with st.form("add_production_form"):
            st.subheader("📬 신규 생산 데이터 등록")

            col1, col2 = st.columns(2)
            with col1:
                brand = st.selectbox("브랜드", ["현대", "기아"])
                region_options = df["공장명(국가)"].dropna().unique().tolist()
                region = st.selectbox("공장명(국가)", ["직접 입력"] + region_options)
                model_options = df["차종"].dropna().unique().tolist()
                model = st.selectbox("차종", ["직접 입력"] + model_options)
            with col2:
                year = st.selectbox("연도", sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}))
                month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
                count = st.number_input("생산량", min_value=0, step=1)


            # ✅ 제출 버튼
            submitted = st.form_submit_button("등록하기")
            if submitted:
                st.success("✅ 생산 데이터가 등록되었습니다!")

                new_col = f"{year}-{month}"
                new_row = pd.DataFrame([{
                    "브랜드": brand,
                    "공장명(국가)": region,
                    "차종": model,
                    new_col: count
                }])

                df = pd.concat([df, new_row], ignore_index=True)

                # 저장
                if brand == "기아":
                    df[df["브랜드"] == "기아"].to_csv("data/processed/기아_해외공장판매실적_전처리.CSV", index=False, encoding="utf-8-sig")
                elif brand == "현대":
                    df[df["브랜드"] == "현대"].to_csv("data/processed/현대_해외공장판매실적_전처리.CSV", index=False, encoding="utf-8-sig")
                    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 기본 현황", "🏭 공장별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 공장 위치 지도", "📊 생산 성장률 분석"
    ])

    # --- 기본 현황 ---
    with tab1:
        # 미리 변수 초기화 (값은 나중에 selectbox로 지정)
        brand_options = df["브랜드"].dropna().unique()
        year_options = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True)

        # 레이아웃 분리
        col1, col2 = st.columns([3, 1])

        with col2:
            brand = st.selectbox("브랜드 선택", brand_options, key="brand_tab1")
            year = st.selectbox("연도 선택", year_options, key="year_tab1")
            factory_list = df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique()
            factory = st.selectbox("공장 선택", factory_list if len(factory_list) > 0 else ["선택 가능한 공장 없음"], key="factory_tab1")
        
        with col1:
            month_cols = [col for col in df.columns if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)]
            df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
            filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]

            if not filtered.empty:
                total_prod = int(filtered[month_cols].sum().sum())
                avg_prod = int(filtered[month_cols].mean().mean())
                model_count = filtered["차종"].nunique()

                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("총 생산량", f"{total_prod:,} 대")
                kpi2.metric("평균 생산량", f"{avg_prod:,} 대")
                kpi3.metric("차종 수", f"{model_count} 종")

                df_melted = filtered.melt(id_vars=["차종"], value_vars=month_cols, var_name="월", value_name="생산량")
                df_melted.dropna(subset=["생산량"], inplace=True)

                if not df_melted.empty:
                    chart = alt.Chart(df_melted).mark_line(point=True).encode(
                        x="월",
                        y="생산량",
                        color="차종"
                    ).properties(width=700, height=400, title="📈 월별 차종 생산 추이 (Line Chart)")
                    st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

        # ✅ col1 밖으로 이동된 부분
        if not filtered.empty:
            with st.expander("📋 원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)
            
            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 현재 데이터 다운로드", data=csv, file_name=f"{brand}_{factory}_{year}_생산실적.csv", mime="text/csv")


        
       
    
    
    # --- 공장별 비교 ---
    with tab2:
        brand = st.selectbox("브랜드 선택 (공장 비교)", df["브랜드"].dropna().unique(), key="brand_tab2")
        year_options = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True)
        year = st.selectbox("연도 선택 (공장 비교)", year_options, key="year_tab2")

        month_cols = [col for col in df.columns if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)]
        df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
        grouped = df[(df["브랜드"] == brand)]

        compare_df = grouped.groupby("공장명(국가)")[month_cols].sum(numeric_only=True)
        compare_df["총생산"] = compare_df.sum(axis=1)
        compare_df = compare_df.reset_index()

        chart = alt.Chart(compare_df).mark_bar().encode(
            x=alt.X("총생산:Q", title="총 생산량"),
            y=alt.Y("공장명(국가):N", sort="-x", title="공장명"),
            color="공장명(국가):N"
        ).properties(width=800, height=500, title=f"🏭 {year}년 {brand} 공장별 총 생산량 비교")
        st.altair_chart(chart, use_container_width=True)

    # --- 연도별 추이 ---
    with tab3:
        st.subheader("📊 공장별 연도별 생산 추이 (Bar Chart)")

        col1, col2 = st.columns([3, 1])

        with col1:
            # 차트는 공장 선택 바로 하단에 배치
            df_brand_factory = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)].copy()
            all_years = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)})

            result = []
            for y in all_years:
                y_str = str(y)
                month_cols = [col for col in df.columns if col.startswith(y_str) and re.match(r"\d{4}-\d{2}", col)]
                df_brand_factory[month_cols] = df_brand_factory[month_cols].apply(pd.to_numeric, errors="coerce")
                total = df_brand_factory[month_cols].sum().sum()
                result.append({"연도": y_str, "총생산": total})

            result_df = pd.DataFrame(result).dropna()

            if not result_df.empty:
                chart = alt.Chart(result_df).mark_bar().encode(
                    x=alt.X("연도:O", title="연도"),
                    y=alt.Y("총생산:Q", title="총 생산량"),
                    color=alt.value("#7E57C2")  # 보라 계열 색상
                ).properties(
                    width=700,
                    height=400,
                    title=f"{brand} - {factory} 연도별 총 생산량 (Bar Chart)"
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("선택한 공장의 연도별 데이터가 없습니다.")
           
        with col2:
            brand = st.selectbox("브랜드 선택 (연도별 추이)", df["브랜드"].dropna().unique(), key="brand_tab3")
            factory = st.selectbox(
                "공장 선택 (연도별 추이)",
                df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(),
                key="factory_tab3"
            )

            




    # --- 목표 달성률 ---
    with tab4:
        st.subheader("🎯 공장별 생산 목표 달성률 분석")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            brand = st.selectbox("브랜드 선택 (목표)", df["브랜드"].dropna().unique(), key="brand_tab4")
        with col2:
            year_options = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True)
            year = st.selectbox("연도 선택 (목표)", year_options, key="year_tab4")
        with col3:
            factory = st.selectbox("공장 선택 (목표)", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(), key="factory_tab4")
        with col4:
            goal = st.number_input("목표 생산량 (대)", min_value=0, step=1000, key="goal_tab4")

        month_cols = [col for col in df.columns if col.startswith(year) and re.match(r"\d{4}-\d{2}", col)]
        df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]

        actual = int(filtered[month_cols].sum().sum()) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0

        col_a, col_b = st.columns([1,1])
        with col_a:
            st.metric("총 생산량", f"{actual:,} 대")
        with col_b:
            st.metric("목표 달성률", f"{rate:.2f}%")

        col_c, col_d = st.columns(2)

        with col_c:
            fig_donut = go.Figure(data=[go.Pie(
                labels=["실제 생산량", "남은 목표"],
                values=[actual, max(goal - actual, 0)],
                hole=0.5,
                marker_colors=["purple", "lightgray"]
            )])
            fig_donut.update_layout(
                title_text="목표 달성률",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30),
                annotations=[dict(text=f"{rate:.1f}%", x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_d:
            fig_bar = go.Figure(data=[
                go.Bar(name="목표", x=["목표"], y=[goal], marker_color="lightblue"),
                go.Bar(name="실제 생산량", x=["목표"], y=[actual], marker_color="purple")
            ])
            fig_bar.update_layout(
                barmode="group",
                title="목표 vs 실제 생산량",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30),
                xaxis_title="데이터 유형",
                yaxis_title="수량 (대)",
                legend_title="데이터"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- 공장 위치 지도 ---
    with tab5:

        # 공장 위치 + 설명 + 생산량 데이터
        data = {
            "공장명(국가)": [
                "울산공장", "아산공장", "전주공장", "앨라배마공장", "중국공장",
                "인도공장", "체코공장", "튀르키예공장", "브라질공장", "싱가포르공장", "인도네시아공장"
            ],
            "국가": [
                "대한민국", "대한민국", "대한민국", "미국", "중국",
                "인도", "체코", "튀르키예", "브라질", "싱가포르", "인도네시아"
            ],
            "위도": [35.546, 36.789, 35.825, 32.806, 39.904, 12.971, 49.743, 40.993, -23.550, 1.352, -6.265],
            "경도": [129.317, 126.987, 127.145, -86.791, 116.407, 77.594, 18.011, 28.947, -46.633, 103.819, 106.917],
            "총생산": [
                1600000, 300000, 200000, 400000, 1050000,
                700000, 300000, 1000000, 250000, 50000, 250000
            ],
            "설명": [
                "세계 최대 단일 자동차 공장. 5개 독립 제조 공장 등 보유.",
                "첨단 자립형 공장. 수출용 승용차 생산 등.",
                "글로벌 상용차 제조 기지. 세계 최대 상용차 생산.",
                "현대 해외 공장 표준 모델.",
                "중국 내 소형차 최다 판매 기록.",
                "신흥 시장 제조 기지.",
                "유럽 시장 전략 차종 생산.",
                "현대자동차 최초 해외 공장.",
                "현지 시장 맞춤 생산.",
                "최초의 스마트 팩토리.",
                "아세안 최초 완성차 공장."
            ]
        }

        location_df = pd.DataFrame(data)

        selected_country = st.selectbox("나라 선택", ["전체"] + sorted(location_df["국가"].unique()), key="country_map")

        if selected_country == "전체":
            filtered_df = location_df.copy()
            detail_df = filtered_df.sort_values("총생산", ascending=False).head(4)  # 상위 4개만
        else:
            filtered_df = location_df[location_df["국가"] == selected_country]
            detail_df = filtered_df  # 전체 표시

        # pydeck 시각화 준비
        view_state = pdk.ViewState(
            latitude=filtered_df["위도"].mean(),
            longitude=filtered_df["경도"].mean(),
            zoom=1 if selected_country == "전체" else 4,
        )

        scatterplot_layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position=["경도", "위도"],
            get_radius=50000,
            get_fill_color=[0, 122, 255],
            pickable=True,
        )

        tooltip = {
            "html": "<b>{공장명(국가)}</b><br>총생산: {총생산} 대<br>{설명}",
            "style": {"backgroundColor": "#f2f2f2", "color": "#333"}
        }

        deck = pdk.Deck(
            layers=[scatterplot_layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=pdk.map_styles.LIGHT
        )

        # 👇 레이아웃 구성: 지도 (4) | 상세정보 (1)
        map_col, info_col = st.columns([4, 1])
        with map_col:
            st.pydeck_chart(deck)

        with info_col:
            st.markdown("#### 📍 상세 정보")
            if detail_df.empty:
                st.info("선택한 나라에 해당하는 공장이 없습니다.")
            else:
                for _, row in detail_df.iterrows():
                    st.markdown(f"**{row['공장명(국가)']}**")
                    st.markdown(f"- 총생산량: {row['총생산']:,} 대")
                    st.markdown(f"- 설명: {row['설명']}")
                    st.markdown("---")



    # --- 생산 성장률 분석 ---
    with tab6:
        col1, col2 = st.columns([1, 1])
        with col1:
            brand = st.selectbox("브랜드 선택 (성장률)", df["브랜드"].dropna().unique(), key="brand_tab6")
       
            year_list = sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)})
        with col2:
            if len(year_list) < 2:
                st.warning("성장률 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
            else:
                year = st.selectbox("기준 연도 선택", year_list[1:], key="year_tab6")
                prev_year = year_list[year_list.index(year) - 1]

        # 전년도와 올해 데이터 필터링
        current = df[(df["브랜드"] == brand)]
        prev_cols = [col for col in df.columns if col.startswith(prev_year) and re.match(r"\d{4}-\d{2}", col)]
        curr_cols = [col for col in df.columns if col.startswith(year) and re.match(r"\d{4}-\d{2}", col)]

        current[prev_cols + curr_cols] = current[prev_cols + curr_cols].apply(pd.to_numeric, errors="coerce")

        # 공장별 합계 계산
        prev_sum = current.groupby("공장명(국가)")[prev_cols].sum().sum(axis=1).rename("전년도")
        curr_sum = current.groupby("공장명(국가)")[curr_cols].sum().sum(axis=1).rename("기준년도")

        # 병합 및 성장률 계산
        merged = pd.concat([prev_sum, curr_sum], axis=1).dropna()
        merged["성장률"] = ((merged["기준년도"] - merged["전년도"]) / merged["전년도"] * 100).round(2)
        merged = merged.reset_index()

        # 테이블 및 시각화
        top5 = merged.sort_values("성장률", ascending=False).head(5)
        bottom5 = merged.sort_values("성장률").head(5)

        st.markdown(f"#### 📈 {prev_year} → {year} 성장률 상위 5개 공장")
        st.dataframe(top5, use_container_width=True)

        st.markdown(f"#### 📉 {prev_year} → {year} 성장률 하위 5개 공장")
        st.dataframe(bottom5, use_container_width=True)

        chart = alt.Chart(merged).mark_bar().encode(
            x=alt.X("성장률:Q", title="성장률 (%)"),
            y=alt.Y("공장명(국가):N", sort="-x"),
            color=alt.condition("datum.성장률 > 0", alt.value("#2E8B57"), alt.value("#DC143C"))
        ).properties(
            title=f"📊 {prev_year} → {year} 공장별 생산 성장률",
            width=800,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
