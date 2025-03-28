import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import urllib3
import re
import ace_tools_open as tools

# 수출관리 

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 데이터 로드 함수 - 캐시 처리
@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"csv 파일 로드 중 오류 발생: {str(e)}")
        return None

# 데이터 병합 함수 (수출 실적)
def load_and_merge_export_data(hyundai_path="data/processed/hyundai-by-region.csv", 
                                kia_path="data/processed/kia-by-region.csv"):
    df_h = load_csv(hyundai_path)
    df_k = load_csv(kia_path)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"
    
    # 데이터 병합
    df = pd.concat([df_h, df_k], ignore_index=True)
    
    # '연도' 컬럼 추가
    df = extract_year_column(df)  # 연도 컬럼 추가
    
    
    return df

# 월별 컬럼 추출 함수
def extract_month_columns(df):
    return [col for col in df.columns if "-" in col and col[:4].isdigit()]

# 연도 리스트 추출 함수
def extract_year_list(df):
    return sorted({
        int(col.split("-")[0])
        for col in df.columns
        if re.match(r"\d{4}-\d{2}", col)
    })

# 월 리스트 추출 함수 (특정 연도에 대해)
def extract_month_list(df, year: int):
    return sorted({
        int(col.split("-")[1])
        for col in df.columns
        if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)
    })

# 연도 컬럼 추가 함수
def extract_year_column(df):
    # 월별 컬럼을 가져오는 함수
    month_cols = extract_month_columns(df)
    
    # '연도' 컬럼이 없으면 추가
    if "연도" not in df.columns:
        def get_year(row):
            # 유효한 월별 컬럼을 통해 연도 추출
            valid_years = [int(col.split("-")[0]) for col in month_cols if pd.notnull(row[col])]
            return max(valid_years) if valid_years else None
        
        # '연도' 컬럼 추가
        df["연도"] = df.apply(get_year, axis=1)
    
    # NaN 값이 있는 '연도' 컬럼을 '전체'로 대체 (필요한 경우)
    df["연도"].fillna('전체', inplace=True)

    return df

# 필터링 UI 생성 함수
def get_filter_values(df, key_prefix):
    brand = st.selectbox(f"브랜드 선택", df["브랜드"].dropna().unique(), key=f"{key_prefix}_brand")
    
    # 연도 추출 함수가 반환한 연도 리스트를 제대로 반영
    year_list = extract_year_list(df)
    year = st.selectbox(f"연도 선택", year_list[::-1], key=f"{key_prefix}_year")
    
    # 국가 선택 UI
    country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
    country = st.selectbox(f"국가 선택", country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"], key=f"{key_prefix}_country")
    
    return brand, year, country


# 수출 UI ======================== 메인화면 시작 함수 
def export_ui():
    # 데이터 로드
    df = load_and_merge_export_data()
    if df is None:
        st.error(" 수출 데이터를 불러오지 못했습니다.")
        return

    month_cols = extract_month_columns(df)
    year_list = extract_year_list(df)
    

    # ✅ 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "수출실적 대시보드", "국가별 비교", "연도별 추이", "목표 달성률", "수출 지도", "성장률 분석"
    ])

    # ✅ 수출 등록 토글 함수
    def toggle_export_form():
        st.session_state["show_export_form"] = not st.session_state.get("show_export_form", False)

    # --- 탭 1: 수출 실적 대시보드 ---
    with tab1:
        # 등록 버튼 (토글)
        btn_label = "등록 취소" if st.session_state.get("show_export_form", False) else " 수출 등록"
        st.button(btn_label, on_click=toggle_export_form)

        # 수출 등록 폼 표시
        if st.session_state.get("show_export_form", False):
            with st.form("add_export_form"):
                st.subheader(" 신규 수출 데이터 등록")

                col1, col2 = st.columns(2)
                with col1:
                    brand = st.selectbox("브랜드", ["현대", "기아"])
                    country_options = df["지역명"].dropna().unique().tolist()
                    country = st.selectbox("국가명", ["직접 입력"] + country_options)
                    type_options = df["차량 구분"].dropna().unique().tolist()
                    car_type = st.selectbox("차량 구분", ["직접 입력"] + type_options)
                with col2:
                    year = st.selectbox("연도", sorted({col.split("-")[0] for col in df.columns if "-" in col}), key="exp_year")
                    month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], key="exp_month")
                    count = st.number_input("수출량", min_value=0, step=1)

                submitted = st.form_submit_button("등록하기")
                if submitted:
                    st.success("수출 데이터가 등록되었습니다!")

                    new_col = f"{year}-{month}"
                    new_row = pd.DataFrame([{
                        "브랜드": brand,
                        "지역명": country,
                        "차량 구분": car_type,
                        new_col: count
                    }])

                    df = pd.concat([df, new_row], ignore_index=True)

                    # 저장
                    if brand == "기아":
                        df[df["브랜드"] == "기아"].to_csv("data/processed/kia-by-region.csv", index=False, encoding="utf-8-sig")
                    elif brand == "현대":
                        df[df["브랜드"] == "현대"].to_csv("data/processed/hyundai-by-region.csv", index=False, encoding="utf-8-sig")

        # 월 컬럼 추출
        month_cols = extract_month_columns(df)

        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_1")

        if not year:  # 만약 'year'가 선택되지 않았다면 경고 메시지 출력
            st.warning("연도를 선택해야 합니다.")
            return
        
        # 월 필터링 컬럼
        month_filter_cols = [col for col in month_cols if col.startswith(str(year))]
        filtered = df[(df["브랜드"] == brand) & (df["지역명"] == country)]

        if not filtered.empty:
            total_export = int(filtered[month_filter_cols].sum(numeric_only=True).sum(skipna=True))
            avg_export = int(filtered[month_filter_cols].mean(numeric_only=True).mean(skipna=True))
            type_count = filtered["차량 구분"].nunique()

            # 월별 수출량 차트
            df_melted = filtered.melt(id_vars=["차량 구분"], value_vars=month_filter_cols, var_name="월", value_name="수출량")
            df_melted.dropna(subset=["수출량"], inplace=True)

            if not df_melted.empty:
                fig = px.line(
                    df_melted,
                    x="월",
                    y="수출량",
                    color="차량 구분",
                    markers=True,
                    line_shape="spline",  # 곡선 형태
                    title="차량 구분별 수출량 변화 추이"
                )
                fig.update_layout(
                    xaxis_title="월",
                    yaxis_title="수출량",
                    height=500,
                    template="plotly_white"
                )

                st.plotly_chart(fig, use_container_width=True)
            # 추가 정보 표시
            st.info(f"{year}년 {brand} {country} 수출 실적 ")
            col1, col2, col3= st.columns(3)
            col1.info(f"총 수출량: {total_export:,} 대")
            col2.info(f"평균 수출량: {avg_export:,} 대")
            col3.info(f"차량 구분 수: {type_count} 종")

            st.markdown("---")
        
            # 원본 데이터 보기
            with st.expander("원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)

            # CSV 다운로드
            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("현재 데이터 다운로드", data=csv, file_name=f"{brand}_{country}_{year}_수출실적.csv", mime="text/csv")
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")


    # --- 국가별 비교 ---
    with tab2:
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_2")

        # 데이터 필터링 확인
        grouped = df[(df["브랜드"] == brand) & (df["연도"] == year)]
        
        # 필터링된 데이터가 있는지 확인
        if grouped.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        else:
            # 그룹화 및 총수출 계산
            compare_df = grouped.groupby("지역명")[month_cols].sum(numeric_only=True)
            compare_df["총수출"] = compare_df.sum(axis=1)
            compare_df = compare_df.reset_index()

            # 차트 그리기
            if not compare_df.empty:
                chart = alt.Chart(compare_df).mark_bar().encode(
                    x=alt.X("총수출:Q", title="총 수출량"),
                    y=alt.Y("지역명:N", sort="-x", title="지역명"),
                    color="지역명:N"
                ).properties(width=800, height=500, title="국가별 총 수출량 비교")
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("수출량 데이터가 없습니다.")


                

    # --- 연도별 추이 ---
    with tab3:
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_3")

        yearly = df[(df["브랜드"] == brand) & (df["지역명"] == country)]
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
        st.subheader("🎯 목표 수출 달성률")
        brand, year, country = get_filter_values(df, "export_4")
        goal = st.number_input("🎯 수출 목표 (대)", min_value=0, step=1000000, value=5000000)

        # 데이터 필터링
        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["지역명"] == country)]
        actual = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True)) if not filtered.empty else 0
        rate = round((actual / goal * 100), 2) if goal > 0 else 0

        # 동적 색상 설정
        if rate < 50:
            bar_color = "#FF6B6B"  # 빨강
            step_colors = ["#FFE8E8", "#FFC9C9", "#FFAAAA"]  # 연한 빨강 계열
        elif rate < 75:
            bar_color = "#FFD93D"  # 주황
            step_colors = ["#FFF3CD", "#FFE69C", "#FFD96B"]  # 연한 주황 계열
        else:
            bar_color = "#6BCB77"  # 초록
            step_colors = ["#E8F5E9", "#C8E6C9", "#A5D6A7"]  # 연한 초록 계열

        # 게이지 차트 생성
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=rate,
            title={'text': f"{year}년 {brand} {country} 목표 달성률"},
            delta={'reference': 100},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': bar_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 33], 'color': step_colors[0]},
                    {'range': [33, 66], 'color': step_colors[1]},
                    {'range': [66, 100], 'color': step_colors[2]}
                ],
                'threshold': {
                    'line': {'color': "darkred", 'width': 4},
                    'thickness': 0.75,
                    'value': rate
                }
            }
        ))


        fig_gauge.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="white",
            font=dict(color="darkblue", size=16)
        )

        # 차트 출력
        st.plotly_chart(fig_gauge, use_container_width=True)

        # 추가 정보 표시
        st.write("### 추가 정보")
        col1, col2,col3 = st.columns(3)
        col1.info(f"**목표 수출량**\n\n{goal:,} 대")
        col2.info(f"**실제 수출량**\n\n{actual:,} 대")
        col3.info(f"**목표 달성률**\n\n{rate:.2f}%")

        # 원본 데이터 보기
        with st.expander("📋 원본 데이터 보기"):
            st.dataframe(filtered, use_container_width=True)


    # --- 수출 지도 ---
    with tab5:

        # 📌 확장된 공장 → 수출국 데이터 정의 (공장 설명 포함)
        flow_data = {
            "공장명": [
                "울산공장", "울산공장", "아산공장", "전주공장", "앨라배마공장", "중국공장",
                "인도공장", "체코공장", "튀르키예공장", "브라질공장", "싱가포르공장", "인도네시아공장"
            ],
            "수출국": [
                "미국", "독일", "사우디아라비아", "호주", "캐나다", "홍콩",
                "인도네시아", "영국", "프랑스", "아르헨티나", "태국", "베트남"
            ],
            "공장_위도": [
                35.546, 35.546, 36.790, 35.824, 32.806, 39.904,
                12.971, 49.523, 40.922, -23.682, 1.352, -6.305
            ],
            "공장_경도": [
                129.317, 129.317, 126.977, 127.148, -86.791, 116.407,
                77.594, 17.642, 29.330, -46.875, 103.819, 107.097
            ],
            "수출국_위도": [
                37.090, 51.165, 23.8859, -25.2744, 56.1304, 22.3193,
                -6.200, 55.3781, 46.6034, -38.4161, 15.8700, 14.0583
            ],
            "수출국_경도": [
                -95.712, 10.4515, 45.0792, 133.7751, -106.3468, 114.1694,
                106.816, -3.4360, 1.8883, -63.6167, 100.9925, 108.2772
            ],
            "공장설명": [
                "단일 자동차 공장 중 세계 최대 규모",
                "5개 독립 제조 공장, 수출 부두 포함",
                "쏘나타, 그랜저 등 수출용 승용차 생산",
                "세계 최초 연료 전지 전기 트럭 제조",
                "북미 생산 기준 표준 공장",
                "중국 소형차 생산 및 베르나 판매 1위",
                "신흥 시장을 위한 전략 차량 생산",
                "유럽 전략 차종 및 i 시리즈 생산",
                "현대차 최초 해외 공장, 100만대 생산",
                "HB20 등 현지 맞춤형 전략 모델 생산",
                "스마트 팩토리, 아이오닉5 제조",
                "아세안 최초 완성차 공장, 최대 25만대"
            ],
            "브랜드컬러": [
                "#1f77b4", "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c",
                "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b"
            ]
        }

        df_flow = pd.DataFrame(flow_data)
        tools.display_dataframe_to_user(name="수출 공장-국가 연결 데이터", dataframe=df_flow)


        # 🎞️ 프레임 데이터 생성
        frames = []
        for i, row in df_flow.iterrows():
            frames.append({
                "frame": i + 1,
                "공장명": row["공장명"],
                "수출국": row["수출국"],
                "위도": row["공장_위도"],
                "경도": row["공장_경도"],
                "역할": "공장"
            })
            frames.append({
                "frame": i + 1,
                "공장명": row["공장명"],
                "수출국": row["수출국"],
                "위도": row["수출국_위도"],
                "경도": row["수출국_경도"],
                "역할": "수출국"
            })

        df_frames = pd.DataFrame(frames)
        df_frames["경로"] = df_frames["공장명"] + " → " + df_frames["수출국"]

        # 🌐 애니메이션 지도 시각화
        fig = px.line_geo(
            df_frames,
            lat="위도",
            lon="경도",
            color="경로",
            line_group="경로",
            animation_frame="frame",
            scope="world",
            hover_name="역할",
            title="✈️ 공장에서 수출국으로의 애니메이션 경로 시각화"
        )
        fig.update_geos(projection_type="natural earth")
        fig.update_layout(height=600)

        # 📍 Streamlit에서 출력
        st.plotly_chart(fig, use_container_width=True)
        
    # --- 성장률 분석 ---
    with tab6:
        st.subheader("📊 국가별 수출 성장률 분석")
        
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_6")
        
        year_list = sorted(df["연도"].dropna().unique())
        
        if len(year_list) < 2:
            st.warning("성장률 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
        else:
            year = st.selectbox("기준 연도 선택", year_list[1:], key="export_year_6")
            prev_year = year_list[year_list.index(year) - 1]

            current = df[(df["브랜드"] == brand) & (df["연도"] == year)]
            previous = df[(df["브랜드"] == brand) & (df["연도"] == prev_year)]

            cur_sum = current.groupby("지역명")[month_cols].sum(numeric_only=True).sum(axis=1).rename("current")
            prev_sum = previous.groupby("지역명")[month_cols].sum(numeric_only=True).sum(axis=1).rename("previous")

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
                y=alt.Y("지역명:N", sort="-x"),
                color=alt.condition("datum.성장률 > 0", alt.value("#2E8B57"), alt.value("#DC143C"))
            ).properties(
                title=f"📊 {prev_year} → {year} 국가별 수출 성장률",
                width=800,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)
