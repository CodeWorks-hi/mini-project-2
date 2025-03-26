import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime, timedelta
import urllib3

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# 이전 평일 계산 함수
def get_previous_weekday(date):
    one_day = timedelta(days=1)
    while True:
        date -= one_day
        if date.weekday() < 5:
            return date

def load_data():
    hyundai = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    kia = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")

    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"

    df = pd.concat([hyundai, kia], ignore_index=True)

    # 월 컬럼 식별
    month_cols = [col for col in df.columns if "-" in col and col[:4].isdigit()]

    # 연도 컬럼이 없는 경우에만 생성
    if "연도" not in df.columns:
        def get_year(row):
            # 행에서 값이 있는 월 컬럼들만 추출
            valid_years = [
                int(col.split("-")[0])
                for col in month_cols
                if pd.notnull(row[col])
            ]
            if valid_years:
                # 여러 연도가 섞인 경우 → 가장 큰 연도로 결정
                return max(valid_years)
            else:
                # 모두 NaN인 경우 → None 또는 원하는 기본값
                return None

        df["연도"] = df.apply(get_year, axis=1)

    return df

def extract_year_list(df):
    # 해당 df의 컬럼 중 'YYYY-MM' 형식에서 연도만 추출 → 정렬
    return sorted({
        int(col.split("-")[0])
        for col in df.columns
        if "-" in col and col[:4].isdigit()
    })

df = load_data()

def export_ui():
    st.title("📨 수출 실적 대시보드")
    st.button("수출 등록")

    month_cols = [col for col in df.columns if "-" in col and col[:4].isdigit()]

    year_list = extract_year_list(df)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "기본 현황", "국가별 비교", "연도별 추이", "목표 달성률", "수출 지도", "성장률 분석", "실시간 환율"
    ])

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_1")
        with col2:
            year = st.selectbox("연도 선택", year_list[::-1], key="export_year_1")
        with col3:
            country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
            country = st.selectbox("국가 선택", country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"], key="export_country_1")

        month_filter_cols = [col for col in month_cols if col.startswith(str(year))]
        filtered = df[(df["브랜드"] == brand) & (df["지역명"] == country)]

        if not filtered.empty:
            total_export = int(filtered[month_filter_cols].sum(numeric_only=True).sum(skipna=True))
            avg_export = int(filtered[month_filter_cols].mean(numeric_only=True).mean(skipna=True))
            type_count = filtered["차량 구분"].nunique()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("총 수출량", f"{total_export:,} 대")
            kpi2.metric("평균 수출량", f"{avg_export:,} 대")
            kpi3.metric("차량 구분 수", f"{type_count} 종")

            df_melted = filtered.melt(id_vars=["차량 구분"], value_vars=month_filter_cols, var_name="월", value_name="수출량")
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
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_2")
        year = st.selectbox("연도 선택 (국가 비교)", sorted(df["연도"].dropna().unique(), reverse=True), key="export_year_2")
        grouped = df[(df["브랜드"] == brand) & (df["연도"] == year)]
        compare_df = grouped.groupby("지역명")[month_cols].sum(numeric_only=True)
        compare_df["총수출"] = compare_df.sum(axis=1)
        compare_df = compare_df.reset_index()

        chart = alt.Chart(compare_df).mark_bar().encode(
            x=alt.X("총수출:Q", title="총 수출량"),
            y=alt.Y("지역명:N", sort="-x", title="지역명"),
            color="지역명:N"
        ).properties(width=800, height=500, title="🌍 국가별 총 수출량 비교")
        st.altair_chart(chart, use_container_width=True)

    # --- 연도별 추이 ---
    with tab3:
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_3")
        country = st.selectbox("국가 선택 (연도별 추이)", df[df["브랜드"] == brand]["지역명"].dropna().unique(), key="export_country_2")
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
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_4")
        year = st.selectbox("연도 선택 (목표)", sorted(df["연도"].dropna().unique(), reverse=True), key="export_year_3")
        country = st.selectbox("국가 선택 (목표)", df[df["브랜드"] == brand]["지역명"].dropna().unique(), key="export_country_3")
        goal = st.number_input("🎯 수출 목표 (대)", min_value=0, step=1000)

        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["지역명"] == country)]
        actual = int(filtered[month_cols].sum(numeric_only=True).sum(skipna=True)) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0

        st.metric("총 수출량", f"{actual:,} 대")
        st.metric("목표 달성률", f"{rate:.2f}%")

    # --- 수출 지도 ---
    with tab5:
        # -----------------------------------------
        # 공장 → 수출국 데이터 정의
        # -----------------------------------------
        flow_data = {
            "공장명": ["울산공장", "울산공장", "앨라배마공장", "인도공장"],
            "수출국": ["미국", "독일", "캐나다", "인도네시아"],
            "공장_위도": [35.546, 35.546, 32.806, 12.971],
            "공장_경도": [129.317, 129.317, -86.791, 77.594],
            "수출국_위도": [37.090, 51.1657, 56.1304, -6.200],
            "수출국_경도": [-95.712, 10.4515, -106.3468, 106.816],
        }

        df_flow = pd.DataFrame(flow_data)

        # -----------------------------------------
        # UI 제목 (카드 스타일)
        # -----------------------------------------
        st.markdown("""
        <div style='background-color:#f4faff; padding:20px; border-radius:10px; margin-bottom:15px;'>
            <h3 style='margin:0;'>🚢 공장에서 수출국으로의 이동 시각화</h3>
            <p style='margin:0; color:gray;'>현대/기아 공장에서 글로벌 주요 수출국으로 향하는 흐름을 화살표로 보여줍니다.</p>
        </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------
        # 지도 시각화 구성
        # -----------------------------------------
        arc_layer = pdk.Layer(
            "ArcLayer",
            data=df_flow,
            get_source_position=["공장_경도", "공장_위도"],
            get_target_position=["수출국_경도", "수출국_위도"],
            get_source_color=[255, 100, 30],
            get_target_color=[30, 144, 255],
            auto_highlight=True,
            width_scale=0.0001,
            get_width=30,
            pickable=True,
        )

        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_flow.drop_duplicates(subset=["공장명"]),
            get_position='[공장_경도, 공장_위도]',
            get_radius=60000,
            get_fill_color=[0, 122, 255, 180],
            pickable=True,
        )

        # -----------------------------------------
        # 초기 지도 뷰 설정
        # -----------------------------------------
        view_state = pdk.ViewState(
            latitude=25,
            longitude=40,
            zoom=1.3,
            pitch=0,
        )

        # -----------------------------------------
        # 지도 렌더링
        # -----------------------------------------
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[scatter_layer, arc_layer],
            initial_view_state=view_state,
            tooltip={"text": "공장: {공장명} → 수출국: {수출국}"}
        ))

    # --- 성장률 분석 ---
    with tab6:
        st.subheader("📊 국가별 수출 성장률 분석")
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_5")
        year_list = sorted(df["연도"].dropna().unique())

        if len(year_list) < 2:
            st.warning("성장률 분석을 위해 최소 2개 연도의 데이터가 필요합니다.")
        else:
            year = st.selectbox("기준 연도 선택", year_list[1:], key="export_year_4")
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
            if isinstance(row, dict) and row.get("result") == 1:  # 딕셔너리인지 확인 후 처리
                try:
                    rate = float(row["deal_bas_r"].replace(",", ""))
                    latitude = float(row.get("latitude", 0))  # 위도 추가 (API에서 제공된 데이터 사용)
                    longitude = float(row.get("longitude", 0))  # 경도 추가 (API에서 제공된 데이터 사용)
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
            st.info("❗ 환율 데이터가 비어있습니다.")
            st.stop()

        df_all = pd.DataFrame(all_rows)

        # ======================
        # 📋 전체 테이블 표시 (위도/경도 제외)
        # ======================
        st.markdown("### 📋 전체 환율 데이터 테이블")
        st.dataframe(df_all[["통화", "통화명", "환율"]], use_container_width=True, hide_index=True)

        # ======================
        # 🌍 지도 시각화 (위도/경도 포함)
        # ======================
        st.markdown("### 🌍 세계 지도에서 환율 정보 보기")

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


