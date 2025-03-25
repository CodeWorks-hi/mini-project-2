import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime, timedelta

# 환율 데이터 불러오기 함수
def fetch_currency_data(date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    try:
        if "open_api" not in st.secrets or "apikey" not in st.secrets["open_api"]:
            st.error("❌ API 키가 설정되지 않았습니다. secrets.toml 파일을 확인해주세요.")
            return None

        api_key = st.secrets["open_api"]["apikey"]
        url = "https://api.currencyapi.com/v3/historical"
        headers = {"apikey": api_key}
        params = {
            "currencies": "EUR,USD,CAD,JPY,GBP,CNY,AUD,CHF,HKD,SGD",
            "date": date,
            "base_currency": "KRW"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if "data" not in data:
            st.error("⚠️ 잘못된 데이터 형식입니다.")
            return None
        return data["data"]

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.error("🔒 요청 제한 초과: 하루 요청 수를 초과했습니다.")
        else:
            st.error(f"🔒 인증 오류: {e.response.status_code} - API 키를 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"❗ 오류 발생: {str(e)}")
        return None


# 🔹 실시간 환율 시각화 (함수로 분리)
def render_exchange_tab():
    st.subheader("💱 주요 통화 환율 시계열 추이")

    major_currencies = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'CAD']
    selected_currencies = st.multiselect("조회할 주요 통화 선택", major_currencies, default=major_currencies, key="currency_selector")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", datetime(2024, 12, 1))
    with col2:
        end_date = st.date_input("종료일", datetime(2025, 3, 25))

    if start_date > end_date:
        st.warning("종료일은 시작일보다 이후여야 합니다.")
        st.stop()

    all_data = []
    current = start_date
    with st.spinner("📡 환율 데이터를 수집 중입니다..."):
        while current <= end_date:
            day_str = current.strftime("%Y-%m-%d")
            data = fetch_currency_data(day_str)
            if data:
                for curr in selected_currencies:
                    if curr in data:
                        all_data.append({
                            "date": day_str,
                            "currency": curr,
                            "rate": data[curr]["value"]
                        })
            current += timedelta(days=1)

    if not all_data:
        st.warning("⚠️ 선택한 기간 동안 환율 데이터를 불러오지 못했습니다.")
        st.stop()

    df_all = pd.DataFrame(all_data)
    df_all["date"] = pd.to_datetime(df_all["date"])

    st.markdown("### 📈 선택한 주요 통화의 환율 변화 추이")
    line_chart = alt.Chart(df_all).mark_line(point=True).encode(
        x=alt.X("date:T", title="날짜"),
        y=alt.Y("rate:Q", title="환율 (1KRW 대비)", scale=alt.Scale(zero=False)),
        color=alt.Color("currency:N", title="통화"),
        tooltip=["date:T", "currency:N", alt.Tooltip("rate:Q", format=".4f")]
    ).properties(
        height=450,
        width=700
    )
    st.altair_chart(line_chart, use_container_width=True)

    st.markdown("### 📋 최신 환율 요약")
    latest = df_all[df_all["date"] == df_all["date"].max()].copy()
    latest.sort_values("currency", inplace=True)
    st.dataframe(
        latest,
        column_config={
            "currency": "통화",
            "rate": st.column_config.NumberColumn("환율", format="%.4f"),
            "date": st.column_config.DateColumn("날짜")
        },
        use_container_width=True,
        hide_index=True
    )


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

    # 실시간 환율 탭
    with tab7:
        render_exchange_tab()
        st.subheader("💱 주요 통화 환율 시계열 추이")

        major_currencies = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'CAD']
        selected_currencies = st.multiselect(
            "조회할 주요 통화 선택",
            major_currencies,
            default=major_currencies,
            key="currency_selector_main"
        )

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", datetime(2024, 12, 1))
        with col2:
            end_date = st.date_input("종료일", datetime(2025, 3, 25))

        if start_date > end_date:
            st.warning("종료일은 시작일보다 이후여야 합니다.")
            st.stop()

        all_data = []
        current = start_date
        with st.spinner("📡 환율 데이터를 수집 중입니다..."):
            while current <= end_date:
                day_str = current.strftime("%Y-%m-%d")
                data = fetch_currency_data(day_str)
                if data:
                    for curr in selected_currencies:
                        if curr in data:
                            all_data.append({
                                "date": day_str,
                                "currency": curr,
                                "rate": data[curr]["value"]
                            })
                current += timedelta(days=1)

        if not all_data:
            st.warning("⚠️ 선택한 기간 동안 환율 데이터를 불러오지 못했습니다.")
            st.stop()

        df_all = pd.DataFrame(all_data)
        df_all["date"] = pd.to_datetime(df_all["date"])

        # 📈 시계열 그래프
        st.markdown("### 📈 선택한 주요 통화의 환율 변화 추이")
        line_chart = alt.Chart(df_all).mark_line(point=True).encode(
            x=alt.X("date:T", title="날짜"),
            y=alt.Y("rate:Q", title="환율 (1KRW 대비)", scale=alt.Scale(zero=False)),
            color=alt.Color("currency:N", title="통화"),
            tooltip=["date:T", "currency:N", alt.Tooltip("rate:Q", format=".4f")]
        ).properties(height=450, width=700)
        st.altair_chart(line_chart, use_container_width=True)

        # 📋 최신 환율 테이블
        st.markdown("### 📋 최신 환율 요약")
        latest = df_all[df_all["date"] == df_all["date"].max()].copy()
        latest.sort_values("currency", inplace=True)
        st.dataframe(
            latest,
            column_config={
                "currency": "통화",
                "rate": st.column_config.NumberColumn("환율", format="%.4f"),
                "date": st.column_config.DateColumn("날짜")
            },
            use_container_width=True,
            hide_index=True
        )


