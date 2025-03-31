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
    col1, col2, col3 = st.columns(3)
    
    with col1:
        brand = st.selectbox(
            "브랜드 선택",
            options=df["브랜드"].dropna().unique(),
            key=f"{key_prefix}_brand"
        )
    
    with col2:
        year_list = extract_year_list(df)
        year = st.selectbox(
            "연도 선택",
            options=year_list[::-1],  # 역순으로 정렬
            index=1,
            key=f"{key_prefix}_year"
        )
    
    with col3:
        country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
        country = st.selectbox(
            "국가 선택",
            options=country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"],
            key=f"{key_prefix}_country"
        )
    
    return brand, year, country

# 수출 UI ======================== 메인화면 시작 함수 
def export_ui():
    # 데이터 로드
    df = load_and_merge_export_data()
    if df is None:
        st.error("❌ 수출 데이터를 불러오지 못했습니다.")
        return

    month_cols = extract_month_columns(df)
    year_list = extract_year_list(df)

    # ✅ 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "수출실적 대시보드", "국가별 비교", "연도별 추이", "목표 달성률", "성장률 분석"
    ])

    # --- 탭 1: 수출 실적 대시보드 ---
    with tab1:
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
            df_melted["월_숫자"] = df_melted["월"].apply(lambda x: int(x.split("-")[1]))

            if not df_melted.empty:
                # 라인차트
                fig_line = px.line(
                    df_melted,
                    x="월",
                    y="수출량",
                    color="차량 구분",
                    markers=True,
                    line_shape="spline",
                    title="차량 구분별 수출량 변화 추이 (라인차트)"
                )
                fig_line.update_layout(
                    xaxis_title="월",
                    yaxis_title="수출량",
                    height=400,
                    template="plotly_white"
                )

                # 📊 바차트
                fig_bar = px.bar(
                    df_melted,
                    x="월",
                    y="수출량",
                    color="차량 구분",
                    barmode="group",
                    title="차량 구분별 수출량 변화 추이 (막대차트)"
                )
                fig_bar.update_layout(
                    xaxis_title="월",
                    yaxis_title="수출량",
                    height=400,
                    template="plotly_white"
                )
                col1, col2 = st.columns([1,1])
                with col1:
                    st.plotly_chart(fig_line, use_container_width=True)
                with col2:
                    st.plotly_chart(fig_bar, use_container_width=True)
            # 추가 정보 표시
            st.info(f"{year}년 {brand} {country} 수출 실적 ")
            col1, col2, col3= st.columns(3)
            col1.info(f"총 수출량: {total_export:,} 대")
            col2.info(f"평균 수출량: {avg_export:,} 대")
            col3.info(f"차량 구분 수: {type_count} 종")

            st.markdown("---")
        
            # 원본 데이터 보기
            with st.expander(" 원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)

            # CSV 다운로드
            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("현재 데이터 다운로드", data=csv, file_name=f"{brand}_{country}_{year}_수출실적.csv", mime="text/csv")
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")


    # --- 탭 2: 국가별 비교 ---
    with tab2:
        st.subheader("국가별 비교")
        col1, col2 = st.columns([1, 3])
    
        with col1:
            brand = st.selectbox(
                "브랜드 선택",
                options=df["브랜드"].dropna().unique(),
                key="select_brand"
            )

        if not brand:
            st.warning("브랜드를 선택해야 합니다.")
            return
        
        grouped = df[df["브랜드"] == brand]
        
        if grouped.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        else:
            compare_df = grouped.groupby("지역명")[month_cols].sum(numeric_only=True).reset_index()
            melted_df = compare_df.melt(id_vars=["지역명"], var_name="월", value_name="수출량")

            fig = px.bar(
                melted_df,
                x="지역명",
                y="수출량",
                color="지역명",
                animation_frame="월",
                title=f"{brand} 국가별 월별 수출량 비교"
            )
            fig.update_layout(height=600, width=800)
            st.plotly_chart(fig, use_container_width=True)

    # --- 연도별 추이 ---
    with tab3:
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            brand = st.selectbox(
                "브랜드 선택",
                options=df["브랜드"].dropna().unique(),
                key="t3_brand"
            )
        
        with col2:
            year_list = extract_year_list(df)
            start_year = st.selectbox(
                "시작 연도 선택",
                options=year_list,
                key="t3_start_year"
            )
        
        with col3:
            year_list = extract_year_list(df)
            end_year = st.selectbox(
                "끝 연도 선택",
                options=year_list[::-1],  # 역순으로 정렬
                index=1,
                key="t3_end_year"
            )
        
        with col4:
            country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
            country = st.selectbox(
                "국가 선택",
                options=country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"],
                key="t3_country"
            )

        # st.dataframe(df)
        if start_year >= end_year :
            st.error("시작 연도는 끝 연도보다 작아야 합니다.")
        else:
            yearly = df[(df["브랜드"] == brand) & (df["지역명"] == country)]

            # 연도 추출
            all_years = sorted({col[:4] for col in df.columns if "-" in col and col[:4].isdigit()})

            # 연도별 총수출량 컬럼 생성
            total_export_by_year = {}

            for y in all_years:
                year_cols = [col for col in df.columns if col.startswith(y) and "-" in col]
                if year_cols:
                    total = yearly[year_cols].sum(numeric_only=True).sum()
                    total_export_by_year[f"{y}-총수출"] = [int(total)]

            # 데이터프레임으로 변환
            export_df = pd.DataFrame(total_export_by_year)
            export_df.insert(0, "지역명", country)
            export_df.insert(0, "브랜드", brand)

            # st.dataframe(export_df)

            # 1. 연도별 총수출 컬럼만 추출
            year_columns = [
                col for col in export_df.columns
                if (
                    col.endswith("-총수출")
                    and col[:4].isdigit()
                    and int(col[:4]) >= start_year
                    and int(col[:4]) <= end_year
                )
            ]

            # 2. melt (wide → long)
            line_df = export_df.melt(
                id_vars=["브랜드", "지역명"],
                value_vars=year_columns,
                var_name="연도", value_name="총수출"
            )

            # 3. '연도' 컬럼에서 '2016-총수출' → '2016' 형태로 정리
            line_df["연도"] = line_df["연도"].str.extract(r"(\d{4})").astype(str)

            # 4. 그래프 그리기
            line_chart = alt.Chart(line_df).mark_line(point=True).encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("총수출:Q", title="총수출"),
                color="지역명:N",  # 여러 지역 비교 시 대비용 (단일 지역이면 무시됨)
                tooltip=["연도", "총수출"]
            ).properties(
                title=f"{export_df.iloc[0]['지역명']} 연도별 총 수출량 추이",
                width=700,
                height=400
            )

            st.altair_chart(line_chart, use_container_width=True)


    # --- 목표 달성률 ---
    with tab4:
        st.subheader("🎯 목표 수출 달성률")
        brand, year, country = get_filter_values(df, "export_4")
        goal = st.number_input(" 수출 목표 (대)", min_value=0, step=10000, value=200000)

        # 1. 연도별 총수출량 컬럼 생성
        all_years = sorted({col[:4] for col in df.columns if "-" in col and col[:4].isdigit()})
        total_export_by_year = {}

        for y in all_years:
            year_cols = [col for col in df.columns if col.startswith(y) and "-" in col]
            yearly_filtered = df[(df["브랜드"] == brand) & (df["지역명"] == country)]
            if year_cols and not yearly_filtered.empty:
                total = yearly_filtered[year_cols].sum(numeric_only=True).sum()
                total_export_by_year[f"{y}-총수출"] = int(total)

        # 2. export_df 생성
        export_df = pd.DataFrame([total_export_by_year])
        export_df.insert(0, "지역명", country)
        export_df.insert(0, "브랜드", brand)

        target_col = f"{year}-총수출"
        actual = int(export_df[target_col].values[0]) if target_col in export_df.columns else 0
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
        with st.expander(" 원본 데이터 보기"):
            st.dataframe(filtered, use_container_width=True)


    # --- 성장률 분석 ---
    with tab5:
        st.subheader("📈 국가별 수출 성장률 분석")

        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            brand = st.selectbox(
                "브랜드 선택",
                options=df["브랜드"].dropna().unique(),
                key="t5_brand"
            )
        
        with col2:
            year_list = extract_year_list(df)
            start_year = st.selectbox(
                "시작 연도 선택",
                options=year_list,
                key="t5_start_year"
            )
        
        with col3:
            year_list = extract_year_list(df)
            end_year = st.selectbox(
                "끝 연도 선택",
                options=year_list[::-1],  # 역순으로 정렬
                index=1,
                key="t5_end_year"
            )
        
        with col4:
            country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
            country = st.selectbox(
                "국가 선택",
                options=country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"],
                key="t5_country"
            )

        # 연도 목록
        year_list = sorted({int(col[:4]) for col in df.columns if "-" in col and col[:4].isdigit()})

        # 연도별 총수출량 계산
        export_by_year = {}
        for y in year_list:
            year_cols = [col for col in df.columns if col.startswith(str(y))]
            filtered = df[(df["브랜드"] == brand) & (df["지역명"] == country)]
            if not filtered.empty:
                total = filtered[year_cols].sum(numeric_only=True).sum()
                export_by_year[y] = total

        # 최소 2개 연도 이상 필요
        if start_year >= end_year:
            st.warning("성장 변화율 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
        else:
            # 데이터프레임 구성 및 성장률 계산
            growth_df = pd.DataFrame({
                "연도": list(export_by_year.keys()),
                "총수출": list(export_by_year.values())
            }).sort_values("연도")

            growth_df["전년대비 성장률(%)"] = growth_df["총수출"].pct_change().round(4) * 100

            # ✅ 선택된 연도 범위로 필터링 (start_year+1부터)
            filtered_growth_df = growth_df[
                (growth_df["연도"] >= start_year) & (growth_df["연도"] <= end_year)
            ]

            # 차트
            line_chart = alt.Chart(filtered_growth_df).mark_line(point=True).encode(
                x="연도:O",
                y=alt.Y("전년대비 성장률(%):Q", title="성장률 (%)"),
                tooltip=["연도", "전년대비 성장률(%)"]
            ).properties(
                title=f"📊 {start_year}년 ~ {end_year}년 {country} 수출 성장률 변화",
                width=700,
                height=400
            )
            st.altair_chart(line_chart, use_container_width=True)
