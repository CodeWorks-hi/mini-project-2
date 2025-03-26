import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import plotly.graph_objects as go
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

def goal_achievement_section(df, month_cols):
    st.title("🎯 목표 달성률")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique())
    with col2:
        year = st.selectbox("연도 선택", sorted(df["연도"].dropna().unique(), reverse=True))
    with col3:
        factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique())
    with col4:
        goal = st.number_input("🎯 생산 목표 (대)", min_value=0, step=1000)

    filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["공장명(국가)"] == factory)]
    actual = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True)) if not filtered.empty else 0
    rate = (actual / goal * 100) if goal > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("총 생산량", f"{actual:,} 대")
    with col2:
        st.metric("목표 달성률", f"{rate:.2f}%")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "목표 달성률"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "purple"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "lightblue"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': goal if goal > 0 else 100
            }
        }
    ))

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

    st.plotly_chart(fig_gauge, use_container_width=True)
    st.plotly_chart(fig_bar, use_container_width=True)

def production_ui():
    st.title("📦 생산 관리 대시보드")
    st.button("+ 생산 등록")

    df = load_data()
    month_cols = [col for col in df.columns if "-" in col and col[:4].isdigit()]
    month_suffixes = [col.split("-")[1] for col in month_cols]

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 기본 현황", "🏭 공장별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 공장 위치 지도", "📊 생산 성장률 분석"
    ])
    
    # --- 기본 현황 ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique())
        with col2:
            # 연도 추출: '2021-01', '2022-03' 등에서 '2021', '2022'만 추출
            years = sorted({
                col.split("-")[0]
                for col in df.columns
                if "-" in col and col[:4].isdigit()
            }, reverse=True)

            year = st.selectbox("연도 선택", years)
        with col3:
            factory_list = df[(df["브랜드"] == brand)]["공장명(국가)"].dropna().unique()
            factory = st.selectbox("공장 선택", factory_list if len(factory_list) > 0 else ["선택 가능한 공장 없음"])

        month_cols = [col for col in df.columns if str(year) in col and "-" in col]
        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)].copy()
        filtered["총생산"] = filtered[month_cols].sum(axis=1)

        if not filtered.empty:
            total_prod = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
            avg_prod = int(filtered[month_cols].mean(numeric_only=True).mean(skipna=True))
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
                ).properties(width=900, height=400, title="📈 월별 차종 생산 추이")
                st.altair_chart(chart, use_container_width=True)

            with st.expander("📋 원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)

            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 현재 데이터 다운로드", data=csv, file_name=f"{brand}_{factory}_{year}_생산실적.csv", mime="text/csv")
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # --- 공장별 비교 ---
    with tab2:
        brand = st.selectbox("브랜드 선택 (공장 비교)", df["브랜드"].dropna().unique())
        years = sorted({
                col.split("-")[0]
                for col in df.columns
                if "-" in col and col[:4].isdigit()
        }, reverse=True)

        year = st.selectbox("연도 선택", years, key="year_select_factory")
        # 필요한 고정 컬럼 지정
        id_columns = [col for col in df.columns if not "-" in col or not col[:4].isdigit()]

        df_long = df.melt(
            id_vars=id_columns,
            var_name="연월",
            value_name="생산량"
        )

        df_long["연도"] = df_long["연월"].str[:4].astype(int)
        df_long["월"] = df_long["연월"].str[5:].astype(int)
        filtered = df_long[
            (df_long["브랜드"] == brand) &
            (df_long["연도"] == year)
        ]

        grouped = filtered.groupby("공장명(국가)")["생산량"].sum().reset_index()
        # 연도 선택
        year = st.selectbox("연도 선택", years, index=0, key="year_select_fact")

        # 월 컬럼 추출
        month_cols = [col for col in df.columns if col.startswith(str(year)) and "-" in col]

        # 유효성 검사
        if not month_cols:
            st.warning(f"{year}년 월별 생산 데이터가 없습니다.")
            st.stop()

        # 그룹화 및 집계
        grouped = df.groupby("공장명(국가)")[month_cols].sum(numeric_only=True)
        compare_df = df.groupby("공장명(국가)")[month_cols].sum(numeric_only=True)
        compare_df["총생산"] = compare_df.sum(axis=1)
        compare_df = compare_df.reset_index()

        chart = alt.Chart(compare_df).mark_bar().encode(
            x=alt.X("총생산:Q", title="총 생산량"),
            y=alt.Y("공장명(국가):N", sort="-x", title="공장명"),
            color="공장명(국가):N"
        ).properties(width=800, height=500, title="🏭 공장별 총 생산량 비교")
        st.altair_chart(chart, use_container_width=True)

    # --- 연도별 추이 ---
    with tab3:
        brand = st.selectbox("브랜드 선택 (연도별 추이)", df["브랜드"].dropna().unique())
        factory = st.selectbox("공장 선택 (연도별 추이)", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique())
        yearly = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        id_cols = [col for col in yearly.columns if not "-" in col or not col[:4].isdigit()]
        
        yearly = yearly.melt(
            id_vars=id_cols,
            var_name="연월",
            value_name="생산량"
        )
        yearly["연도"] = yearly["연월"].str[:4].astype(int)
        yearly["월"] = yearly["연월"].str[5:].astype(int)

        yearly_sum = yearly.groupby("연도")["생산량"].sum().reset_index()
        yearly_sum["총생산"] = yearly_sum["생산량"]

        line_chart = alt.Chart(yearly_sum).mark_line(point=True).encode(
            x="연도:O",
            y="총생산:Q"
        ).properties(title="📈 연도별 총 생산량 변화 추이", width=700, height=400)
        st.altair_chart(line_chart, use_container_width=True)

    # --- 목표 달성률 ---
    with tab4:

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="brand_select_goal")
        with col2:
            year = st.selectbox("연도 선택", years, index=0, key="year_select_goal")
        with col3:
            factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(), key="factory_select_goal")
        with col4:
            goal = st.number_input("🎯 생산 목표 (대)", min_value=0, step=1000, key="goal_input")

        # 데이터 필터링 및 계산
        filtered = df_long[
            (df_long["브랜드"] == brand) &
            (df_long["연도"] == year) &
            (df_long["공장명(국가)"] == factory)
        ]

        actual = int(filtered["생산량"].sum(skipna=True)) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0

        # KPI 카드 섹션
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 생산량", f"{actual:,} 대")
        with col2:
            st.metric("목표 달성률", f"{rate:.2f}%")

        # 게이지 차트 생성 (Plotly 사용)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "목표 달성률"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "lightblue"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': goal if goal > 0 else 100
                }
            }
        ))

        # 막대 차트 생성 (Plotly 사용)
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

        # 시각화 표시
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.plotly_chart(fig_bar, use_container_width=True)
    

    # --- 공장 위치 지도 ---
    # 데이터 생성
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
            "세계 최대 단일 자동차 공장. 5개 독립 제조 공장, 엔진 및 트랜스미션 공장, 수출 부두, 품질 관리 센터 보유.",
            "첨단 자립형 공장. 쏘나타, 그랜저(Azera) 등 수출용 승용차 생산. 친환경 태양열 루프탑 농장 운영.",
            "글로벌 상용차 제조 기지. 세계 최대의 상용차 생산 공장. 세계 최초 연료 전지 전기 트럭 제조.",
            "현대자동차 해외 공장의 표준 모델. Harbor Report의 북미 자동차 생산 조사에서 6년 연속 최고의 공장으로 선정.",
            "3개 공장의 연 생산량 1,050,000대. 제4공장과 제5공장 설립 예정. 베르나로 중국 내 소형차 최다 판매 기록.",
            "인도 등 신흥 시장을 위한 제조 기지. 플렉서블 엔진 공장 운영. EON, i10, i20 등 전략 차량 생산.",
            "i 시리즈 등 유럽 시장에 맞는 전략적인 차종 생산. 체코 국가 품질상 '엑설런스 상' 수상.",
            "현대자동차에서 가장 오래된 해외 공장으로 총생산량이 높은 기지.",
            "상파울루에 위치한 HB20 등 현지 시장에 맞는 전략적인 차종 생산.",
            "현대차그룹 최초의 스마트 팩토리로 아이오닉5 로보택시 제조.",
            "브카시 델타마스 공단에 위치하며 아세안 지역 최초의 완성차 공장."
        ]
    }

    # 데이터프레임 생성
    location_df = pd.DataFrame(data)

    with tab5:
        st.subheader("🗺️ 공장별 위치 기반 생산량 시각화")

            # 나라 선택 박스 추가
        selected_country = st.selectbox("나라를 선택하세요:", ["전체"] + list(location_df["국가"].unique()))

        # 선택한 나라에 따라 데이터 필터링
        if selected_country == "전체":
            filtered_df = location_df
        else:
            filtered_df = location_df[location_df["국가"] == selected_country]

        # 지도 시각화 설정
        view_state = pdk.ViewState(
            latitude=filtered_df["위도"].mean(),
            longitude=filtered_df["경도"].mean(),
            zoom=1 if selected_country == "전체" else 4,
        )

        scatterplot_layer = pdk.Layer(
            type="ScatterplotLayer",
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

        r = pdk.Deck(
            layers=[scatterplot_layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=pdk.map_styles.LIGHT # 밝은 지도 스타일 설정
        )

        st.pydeck_chart(r)

        # 추가 정보 표시
        st.subheader("📍 선택한 나라의 상세 정보")
        for _, row in filtered_df.iterrows():
            st.write(f"**{row['공장명(국가)']}**")
            st.write(f"- 총생산량: {row['총생산']} 대")
            st.write(f"- 설명: {row['설명']}")


    # --- 생산 성장률 분석 ---
    with tab6:
        st.subheader("📊 공장별 생산 성장률 분석")
        brand = st.selectbox("브랜드 선택 (성장률)", df["브랜드"].dropna().unique())
        year_list = sorted({
            col.split("-")[0]
            for col in df.columns
            if "-" in col and col[:4].isdigit()
        })

        if len(year_list) < 2:
            st.warning("성장률 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
        else:
            # 연도 선택
            year = st.selectbox("기준 연도 선택", year_list[1:])  # 최소 2개 이상 존재해야 함
            prev_year = year_list[year_list.index(year) - 1]

            # long 포맷 기준 필터링
            current = df_long[
                (df_long["브랜드"] == brand) &
                (df_long["연도"] == year)
            ]

            previous = df_long[
                (df_long["브랜드"] == brand) &
                (df_long["연도"] == prev_year)
            ]

            cur_sum = current.groupby("공장명(국가)")["생산량"].sum().rename("current")
            prev_sum = previous.groupby("공장명(국가)")["생산량"].sum().rename("previous")

            merged = pd.concat([cur_sum, prev_sum], axis=1).dropna()
            merged["성장률"] = ((merged["current"] - merged["previous"]) / merged["previous"] * 100).round(2)
            merged = merged.reset_index()

            top5 = merged.sort_values("성장률", ascending=False).head(5)
            bottom5 = merged.sort_values("성장률").head(5)

            st.markdown(f"#### {prev_year} → {year} 성장률 상위 공장")
            st.dataframe(top5, use_container_width=True)

            st.markdown(f"#### {prev_year} → {year} 성장률 하위 공장")
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