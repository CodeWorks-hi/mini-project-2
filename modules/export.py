import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime, timedelta
import urllib3

# 수출관리 
# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 이전 평일 계산 함수
def get_previous_weekday(date):
    one_day = timedelta(days=1)
    while True:
        date -= one_day
        if date.weekday() < 5:
            return date

# 환율 데이터 조회 함수
def fetch_exim_exchange(date, api_key):
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        "authkey": api_key,
        "searchdate": date.strftime("%Y%m%d"),
        "data": "AP01"
    }
    try:
        response = requests.get(url, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        st.error(f"\u2757 API 호출 오류: {e}")
        return None

# 데이터 로드 함수 - 캐시 처리
@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
        return None

# 연도 컬럼 추가 함수
def extract_year_column(df):
    month_cols = extract_month_columns(df)
    if "연도" not in df.columns:
        def get_year(row):
            valid_years = [int(col.split("-")[0]) for col in month_cols if pd.notnull(row[col])]
            return max(valid_years) if valid_years else None
        df["연도"] = df.apply(get_year, axis=1)
    
    # NaN 값이 있는 연도 컬럼을 '전체'로 대체 (필요한 경우)
    df["연도"].fillna('전체', inplace=True)
    return df

# NaN 값을 0으로 채우는 함수
def fillna_with_zero(df):
    return df.fillna(0)

# 데이터 병합 함수 (수출 실적)
def load_and_merge_export_data(hyundai_path="data/processed/현대_지역별수출실적_전처리.CSV", 
                                kia_path="data/processed/기아_지역별수출실적_전처리.CSV"):
    df_h = load_csv(hyundai_path)
    df_k = load_csv(kia_path)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"
    
    # 데이터 병합 후 NaN 값 처리
    df_merged = pd.concat([df_h, df_k], ignore_index=True)
    df_merged = fillna_with_zero(df_merged)  # NaN 값을 0으로 처리
    
    return df_merged

# 월별 컬럼 추출 함수
def extract_month_columns(df):
    return [col for col in df.columns if "-" in col and col[:4].isdigit()]

# 연도 리스트 추출 함수
def extract_year_list(df):
    years = sorted({
        int(col.split("-")[0])
        for col in df.columns
        if "-" in col and col[:4].isdigit()
    })
    return years

# 필터링 UI 생성 함수
def get_filter_values(df, key_prefix):
    # 브랜드 선택
    brand_options = sorted(df["브랜드"].dropna().unique())
    brand = st.selectbox(f"브랜드 선택", brand_options, key=f"{key_prefix}_brand")

    # 연도 선택
    year_list = extract_year_list(df)
    year = st.selectbox(f"연도 선택", year_list[::-1], key=f"{key_prefix}_year")

    # 국가 선택
    country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
    country = st.selectbox(f"국가 선택", country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"], key=f"{key_prefix}_country")
    
    return brand, year, country

# 수출 관리
def export_ui():
    df = load_and_merge_export_data()
    if df is None:
        st.error("❌ 수출 데이터를 불러오지 못했습니다.")
        return

    month_cols = extract_month_columns(df)
    year_list = extract_year_list(df)

    # ✅ 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "수출실적 대시보드", "국가별 비교", "연도별 추이", "목표 달성률", "수출 지도", "성장률 분석", "실시간 환율"
    ])

    # ✅ 수출 등록 토글 함수
    def toggle_export_form():
        st.session_state["show_export_form"] = not st.session_state.get("show_export_form", False)

    # --- 탭 1: 수출 실적 대시보드 ---
    with tab1:
        btn_label = "등록 취소" if st.session_state.get("show_export_form", False) else "📥 수출 등록"
        st.button(btn_label, on_click=toggle_export_form)

        if st.session_state.get("show_export_form", False):
            with st.form("add_export_form"):
                st.subheader("📬 신규 수출 데이터 등록")

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
                        df[df["브랜드"] == "기아"].to_csv("data/processed/기아_지역별수출실적_전처리.CSV", index=False, encoding="utf-8-sig")
                    elif brand == "현대":
                        df[df["브랜드"] == "현대"].to_csv("data/processed/현대_지역별수출실적_전처리.CSV", index=False, encoding="utf-8-sig")

        # 월 컬럼 추출
        month_cols = extract_month_columns(df)

        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_1")

        # 월 필터링 컬럼
        month_filter_cols = [col for col in month_cols if col.startswith(str(year))]
        filtered = df[(df["브랜드"] == brand) & (df["지역명"] == country)]

        if not filtered.empty:
            total_export = int(filtered[month_filter_cols].sum(numeric_only=True).sum(skipna=True))
            avg_export = int(filtered[month_filter_cols].mean(numeric_only=True).mean(skipna=True))
            type_count = filtered["차량 구분"].nunique()

            # KPI
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric(label="총 수출량", value=f"{total_export:,} 대")
            kpi2.metric(label="평균 수출량", value=f"{avg_export:,} 대")
            kpi3.metric(label="차량 구분 수", value=f"{type_count} 종")

            # 월별 수출량 차트
            df_melted = filtered.melt(id_vars=["차량 구분"], value_vars=month_filter_cols, var_name="월", value_name="수출량")
            df_melted.dropna(subset=["수출량"], inplace=True)

            if not df_melted.empty:
                chart = alt.Chart(df_melted).mark_line(point=True).encode(
                    x="월",
                    y="수출량",
                    color="차량 구분"
                ).properties(width=900, height=400, title="📈 월별 차량 구분 수출 추이")
                st.altair_chart(chart, use_container_width=True)

            # 원본 데이터 보기
            with st.expander("📋 원본 데이터 보기"):
                st.dataframe(filtered, use_container_width=True)

            # CSV 다운로드
            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 현재 데이터 다운로드", data=csv, file_name=f"{brand}_{country}_{year}_수출실적.csv", mime="text/csv")
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # --- 국가별 비교 ---
    with tab2:
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_2")

        # 연도 컬럼 추가 (필요시)
        df = extract_year_column(df)

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
                ).properties(width=800, height=500, title="🌍 국가별 총 수출량 비교")
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("수출량 데이터가 없습니다.")

    # --- 연도별 추이 ---
    with tab3:
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_3")

        # 데이터 필터링
        yearly = df[(df["브랜드"] == brand) & (df["지역명"] == country)]
        
        if yearly.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        else:
            yearly_sum = yearly.groupby("연도")[month_cols].sum(numeric_only=True)
            yearly_sum["총수출"] = yearly_sum.sum(axis=1)
            yearly_sum = yearly_sum.reset_index()

            # KPI 카드 (연도별 총 수출량 및 평균 수출량)
            total_export = yearly_sum["총수출"].sum()
            avg_export = yearly_sum["총수출"].mean()
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("총 수출량", f"{total_export:,} 대")
            kpi2.metric("평균 수출량", f"{avg_export:,.0f} 대")

            # 차트 그리기
            line_chart = alt.Chart(yearly_sum).mark_line(point=True).encode(
                x="연도:O",
                y="총수출:Q"
            ).properties(title="📈 연도별 총 수출량 변화 추이", width=700, height=400)

            st.altair_chart(line_chart, use_container_width=True)

            # 원본 데이터 보기
            with st.expander("📋 원본 데이터 보기"):
                st.dataframe(yearly_sum, use_container_width=True)



    # --- 목표 달성률 ---
    with tab4:
        # 필터링 UI 호출
        brand, year, country = get_filter_values(df, "export_4")

        goal = st.number_input("🎯 수출 목표 (대)", min_value=0, step=1000)

        # 필터링된 데이터
        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["지역명"] == country)]
        
        # 실제 수출량 계산
        actual = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True)) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0

        # KPI 카드
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("총 수출량", f"{actual:,} 대")
        kpi2.metric("목표 달성률", f"{rate:.2f}%")

        # 목표 미달 경고 (목표 미달 또는 목표 초과)
        if rate < 100:
            st.warning(f"⚠️ 목표 달성률이 100% 미만입니다! 목표에 도달하기 위해 더 많은 수출이 필요합니다.")
        elif rate == 100:
            st.success(f"🎯 목표를 100% 달성했습니다!")
        else:
            st.success(f"🎯 목표를 초과 달성했습니다! ({rate:.2f}% 목표 초과)")

        # 수출 목표 대비 실적 변화 차트
        data = pd.DataFrame({
            "목표": [goal],
            "실제": [actual]
        })

        st.bar_chart(data, width=600, height=400)

        # 원본 데이터 보기
        with st.expander("📋 원본 데이터 보기"):
            st.dataframe(filtered, use_container_width=True)

   # --- 수출 지도 ---
    with tab5:
        # 공장 → 수출국 데이터 정의
        flow_data = {
            "공장명": ["울산공장", "울산공장", "앨라배마공장", "인도공장"],
            "수출국": ["미국", "독일", "캐나다", "인도네시아"],
            "공장_위도": [35.546, 35.546, 32.806, 12.971],
            "공장_경도": [129.317, 129.317, -86.791, 77.594],
            "수출국_위도": [37.090, 51.1657, 56.1304, -6.200],
            "수출국_경도": [-95.712, 10.4515, -106.3468, 106.816],
        }

        df_flow = pd.DataFrame(flow_data)

        # UI 제목 (카드 스타일)
        st.markdown("""
        <div style='background-color:#f4faff; padding:20px; border-radius:10px; margin-bottom:15px;'>
            <h3 style='margin:0;'>🚢 공장에서 수출국으로의 이동 시각화</h3>
            <p style='margin:0; color:gray;'>현대/기아 공장에서 글로벌 주요 수출국으로 향하는 흐름을 화살표로 보여줍니다.</p>
        </div>
        """, unsafe_allow_html=True)

        # 지도 시각화 구성 (화살표 경로 추가)
        arc_layer = pdk.Layer(
            "ArcLayer",
            data=df_flow,
            get_source_position=["공장_경도", "공장_위도"],
            get_target_position=["수출국_경도", "수출국_위도"],
            get_source_color=[255, 100, 30],  # 공장 색상
            get_target_color=[30, 144, 255],  # 수출국 색상
            auto_highlight=True,
            width_scale=0.0005,
            get_width=10,  # 선 두께 설정
            pickable=True,
            great_circle=True,  # 곡선으로 선 그리기
            line_width=4,  # 선의 두께를 더 크게 설정
        )

        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_flow.drop_duplicates(subset=["공장명"]),
            get_position='[공장_경도, 공장_위도]',
            get_radius=60000,
            get_fill_color=[0, 122, 255, 180],
            pickable=True,
        )

        # 초기 지도 뷰 설정
        view_state = pdk.ViewState(
            latitude=25,
            longitude=40,
            zoom=1.3,
            pitch=40,  # 3D 효과 적용
        )

        # 지도 렌더링
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[scatter_layer, arc_layer],
            initial_view_state=view_state,
            tooltip={"text": "공장: {공장명} → 수출국: {수출국}"}
        ))


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


    # --- 실시간 환율 탭 ---
    with tab7:
        st.title("💱 실시간 환율 조회 및 지도 시각화")

        # API 키 로드
        try:
            api_key = st.secrets["exim"]["apikey"]
        except KeyError:
            st.error("❌ API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`을 확인해주세요.")
            st.stop()

        # 날짜 선택 UI
        now = datetime.now()
        default_date = get_previous_weekday(now) if now.weekday() >= 5 or now.hour < 11 else now
        selected_date = st.date_input("📆 환율 조회 날짜", default_date.date(), max_value=datetime.today())
        query_date = datetime.combine(selected_date, datetime.min.time())

        # API 호출 및 데이터 처리
        data = fetch_exim_exchange(query_date, api_key)
        if not data or not isinstance(data, list):
            st.warning("⚠️ 해당 날짜의 환율 데이터를 가져올 수 없습니다.")
            st.stop()

        # 데이터프레임 생성
        all_rows = []
        for row in data:
            if isinstance(row, dict) and row.get("result") == 1:
                try:
                    rate = float(row["deal_bas_r"].replace(",", ""))
                    latitude = float(row.get("latitude", 0))
                    longitude = float(row.get("longitude", 0))
                    all_rows.append({
                        "통화": row.get("cur_unit"),
                        "통화명": row.get("cur_nm"),
                        "환율": rate,
                        "위도": latitude,
                        "경도": longitude
                    })
                except Exception as e:
                    st.warning(f"데이터 처리 중 오류 발생: {e}")
                    continue

        if not all_rows:
            st.warning("❗ 처리된 환율 데이터가 없습니다.")
            st.stop()

        df_all = pd.DataFrame(all_rows)

        # 📋 텍스트 요약 시각화
        st.markdown("### 🌐 국가별 환율 요약")
        cols = st.columns(4)
        chunked = [all_rows[i::4] for i in range(4)]
        for i, chunk in enumerate(chunked):
            with cols[i]:
                for row in chunk:
                    st.markdown(f"- {row['통화']} ({row['통화명']}): {row['환율']:,} KRW")

        # 🌍 지도 시각화
        st.markdown("### 🌍 환율 지도 시각화")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_all,
            get_position=["경도", "위도"],
            get_radius=50000,
            get_fill_color=[255, 140, 0],
            pickable=True,
            tooltip={"html": "<b>{통화명}</b><br>환율: {환율} KRW"}
        )

        view_state = pdk.ViewState(
            latitude=20,
            longitude=0,
            zoom=1.5,
            pitch=40
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer]
        ))
