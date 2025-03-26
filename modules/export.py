import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime, timedelta
import certifi
import urllib3

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 전날 평일 계산 함수
def get_previous_weekday(date):
    one_day = timedelta(days=1)
    while True:
        date -= one_day
        if date.weekday() < 5:  # 0~4: 월~금
            return date

# 한국수출입은행 환율 API 호출 함수
def fetch_exim_exchange(date: datetime, api_key: str):
    attempt = 0
    while attempt < 3:
        date_str = date.strftime("%Y%m%d")
        url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
        params = {
            "authkey": api_key,
            "searchdate": date_str,
            "data": "AP01"
        }
        try:
            response = requests.get(url, params=params, verify=False)  # SSL 인증서 검증 비활성화
            response.raise_for_status()
            data = response.json()

            # 응답은 있으나 환율이 없는 경우 (비영업일 등)
            if isinstance(data, list) and all(item.get("deal_bas_r") in [None, ""] for item in data):
                st.warning(f"📭 {date_str}일자 환율 정보가 없습니다. 전날 평일 데이터로 대체합니다.")
                date = get_previous_weekday(date)
                attempt += 1
                continue

            return data, date
        except requests.exceptions.RequestException as e:
            st.error(f"❗ API 호출 오류: {e}")
            return [], date

    return [], date

def export_ui():
    st.title("📤 수출 실적 대시보드")
    st.button("+ 수출 등록")

    # 데이터 로딩
    df = load_data()
    month_cols = [f"{i}월" for i in range(1, 13)]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce')

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 기본 현황", "🌍 국가별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 수출 지도", "📊 성장률 분석", "💱 실시간 환율"
    ])

def export_ui():
    st.title("📤 수출 실적 대시보드")
    st.button("+ 수출 등록")

    # 🔽 데이터 로딩 (중복 정의 방지)
    hyundai = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    kia = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"
    df = pd.concat([hyundai, kia], ignore_index=True)
    month_cols = [f"{i}월" for i in range(1, 13)]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce')

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 기본 현황", "🌍 국가별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 수출 지도", "📊 성장률 분석", "💱 실시간 환율"
    ])


    # --- 기본 현황 ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="export_brand_1")
        with col2:
            year = st.selectbox("연도 선택", sorted(df["연도"].dropna().unique(), reverse=True), key="export_year_1")
        with col3:
            country_list = df[df["브랜드"] == brand]["지역명"].dropna().unique()
            country = st.selectbox("국가 선택", country_list if len(country_list) > 0 else ["선택 가능한 국가 없음"], key="export_country_1")

        filtered = df[(df["브랜드"] == brand) & (df["연도"] == year) & (df["지역명"] == country)]

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
        st.subheader("🗺️ 국가별 수출량 지도 시각화")
        try:
            location_df = pd.read_csv("data/세일즈파일/국가_위치정보_수출.csv")
            export_sum = df.groupby("지역명")[month_cols].sum(numeric_only=True)
            export_sum["총수출"] = export_sum.sum(axis=1)
            export_sum = export_sum.reset_index()
            merged = pd.merge(location_df, export_sum, on="지역명", how="left")
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
                tooltip={"text": "{지역명}\n총수출: {총수출} 대"}
            ))
        except Exception as e:
            st.error(f"지도 시각화 로딩 중 오류 발생: {e}")

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
        st.subheader("💱 한국수출입은행 실시간 환율 조회")

        # API 키 로드
        try:
            api_key = st.secrets["exim"]["apikey"]
        except KeyError:
            st.error("❌ API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`을 확인해주세요.")
            st.stop()

        # 환율 조회 날짜 자동 계산
        now = datetime.now()
        if now.weekday() >= 5 or now.hour < 11:
            default_date = get_previous_weekday(now)
        else:
            default_date = now

        # 날짜 선택 UI
        selected_date = st.date_input("📆 환율 조회 날짜", default_date.date(), max_value=datetime.today())
        query_date = datetime.combine(selected_date, datetime.min.time())

        # API 호출
        data, final_date = fetch_exim_exchange(query_date, api_key)
        if not data:
            st.warning("⚠️ 해당 날짜의 환율 데이터를 가져올 수 없습니다.")
            st.stop()

        # 전체 데이터프레임 생성
        all_rows = []
        for row in data:
            if row.get("result") == 1:
                try:
                    rate = float(row["deal_bas_r"].replace(",", ""))
                    all_rows.append({
                        "날짜": final_date.date(),
                        "통화": row.get("cur_unit"),
                        "통화명": row.get("cur_nm"),
                        "환율": rate
                    })
                except:
                    continue

        if not all_rows:
            st.info("❗ 환율 데이터가 비어있습니다.")
            st.stop()

        df_all = pd.DataFrame(all_rows).sort_values("통화")

        # 전체 테이블 표시
        st.markdown("### 📋 전체 환율 데이터 테이블")
        st.dataframe(df_all, use_container_width=True, hide_index=True)

        # 옵션 목록 정의
        currency_options = ["USD", "EUR", "JPY", "CNY", "GBP", "CAD", "AUD", "CHF", "SGD"]

        # 기본값 설정 (옵션 목록에 있는 값만 사용)
        default_currencies = ["USD", "EUR", "JPY"]

        # multiselect 위젯 생성
        st.markdown("### 🔍 통화 선택 후 상세 조회")
        currency_filter = st.multiselect(
            "조회할 통화 선택",
            options=currency_options,
            default=default_currencies
        )

        filtered_df = df_all[df_all["통화"].isin(currency_filter)]

        if filtered_df.empty:
            st.info("선택한 통화의 환율 정보가 없습니다.")
        else:
            # 차트 시각화
            st.markdown("### 📈 선택한 통화 환율 차트")
            chart = alt.Chart(filtered_df).mark_bar().encode(
                x=alt.X("통화:N", title="통화"),
                y=alt.Y("환율:Q", title="매매 기준율"),
                color=alt.Color("통화:N", title="통화"),
                tooltip=["통화명", "통화", "환율"]
            ).properties(width=700, height=400)
            st.altair_chart(chart, use_container_width=True)

            # 상세 테이블 표시
            st.markdown("### 📄 선택 통화 환율 테이블")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)



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


