import streamlit as st
import pandas as pd
import pydeck as pdk

def dashboard_ui():
    # 📍 데이터 로드
    df_h = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    df_k = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    df = pd.concat([df_h, df_k], ignore_index=True)

    # 📍 국가명 한글 매핑
    country_mapping = {
        "US": "미국", "China": "중국", "Germany": "독일", "Australia": "호주", "Brazil": "브라질",
        "India": "인도", "Canada": "캐나다", "Mexico": "멕시코", "Russia": "러시아", "UK": "영국",
        "EU+EFTA": "유럽연합", "E.Europe/CIS": "동유럽", "Latin America": "중남미",
        "Middle East/Africa": "중동/아프리카", "Asia / Pacific": "아시아/태평양"
    }
    df["국가명_한글"] = df["국가명"].map(country_mapping)
    korean_to_english = {v: k for k, v in country_mapping.items()}

    # 📍 차량 구분별 색상 정의
    color_map = {
        "Passenger Car": [30, 144, 255, 160],
        "Recreational Vehicle": [255, 165, 0, 160],
        "Commercial Vehicle": [34, 139, 34, 160],
        "Special Vehicle": [220, 20, 60, 160],
        "Total": [100, 100, 100, 100],
    }

    # 상단 필터 바 구성 (col1 ~ col7)
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("### Hyundai-Kia ERP")

    with col2:
        st.write("")  # 여백
    with col3:
        st.write("")  # 여백

    with col4:
        year = st.selectbox("연도", sorted(df["연도"].dropna().unique()), key="export_year")

    with col5:
        brand = st.selectbox("브랜드", ["전체", "현대", "기아"], key="export_brand")

    with col6:
        country_kor = st.selectbox("국가 (한글)", ["전체"] + sorted(df["국가명_한글"].dropna().unique()), key="export_country")

    with col7:
        vehicle_type = st.selectbox("차량 구분", ["전체"] + sorted(df["차량 구분"].dropna().unique()), key="export_vehicle")

    # 📍 필터 적용
    df_filtered = df[df["연도"] == year]
    if brand != "전체":
        df_filtered = df_filtered[df_filtered["브랜드"] == brand]
    if country_kor != "전체":
        eng_country = korean_to_english.get(country_kor)
        df_filtered = df_filtered[df_filtered["국가명"] == eng_country]
    if vehicle_type != "전체":
        df_filtered = df_filtered[df_filtered["차량 구분"] == vehicle_type]

    # 📍 월별 합계 → 총수출량 계산
    month_cols = [f"{i}월" for i in range(1, 13)]
    df_filtered["총수출"] = df_filtered[month_cols].sum(axis=1, numeric_only=True)

    # 📍 위치정보 로드 및 병합
    try:
        loc_df = pd.read_csv("data/세일즈파일/국가_위치정보_수출.csv")
        merged = pd.merge(df_filtered, loc_df, on="국가명", how="left")
        merged = merged.dropna(subset=["위도", "경도", "총수출"])
    except Exception as e:
        st.error(f"위치 정보 병합 중 오류: {e}")
        return

    # ✅ 지도 & 카드 Layout
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("🗺️ 국가별 수출 지도")

        # pydeck 표시
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1.3),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=merged,
                    get_position='[경도, 위도]',
                    get_radius='총수출 / 5',
                    get_fill_color=f"[{color_map.get(vehicle_type, [60,60,60,150])[0]}, {color_map.get(vehicle_type, [60,60,60,150])[1]}, {color_map.get(vehicle_type, [60,60,60,150])[2]}, 160]",
                    pickable=True
                )
            ],
            tooltip={"text": "{국가명_한글}\n차량: {차량 구분}\n수출량: {총수출} 대"}
        ))

    with right_col:
        st.subheader("📦 국가별 수출 요약")
        top = merged.sort_values("총수출", ascending=False).head(3)
        bottom = merged.sort_values("총수출").head(3)

        st.markdown("#### 🚀 상위 국가")
        for i, row in top.iterrows():
            st.metric(f"{row['국가명_한글']} ({row['차량 구분']})", f"{int(row['총수출']):,} 대")

        st.markdown("#### 🐢 하위 국가")
        for i, row in bottom.iterrows():
            st.metric(f"{row['국가명_한글']} ({row['차량 구분']})", f"{int(row['총수출']):,} 대")
