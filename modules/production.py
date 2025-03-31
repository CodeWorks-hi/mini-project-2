import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import time

# 생산관리 

# 데이터 로딩
@st.cache_data
def load_data():
    hyundai = pd.read_csv("data/processed/hyundai-by-plant.csv")
    kia = pd.read_csv("data/processed/kia-by-plant.csv")

    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"

    for df in [hyundai, kia]:
        if "차종" not in df.columns:
            df["차종"] = "기타"
        numeric_cols = df.select_dtypes(include=['number']).columns
        df.loc[df[numeric_cols].sum(axis=1) == 0, "차종"] = "기타"

    return pd.concat([hyundai, kia], ignore_index=True)


# 생산 대시보드 UI
def production_ui():
    df = load_data()
    tab1, tab2, tab3, tab4 = st.tabs([
        "기본 현황", "공장별 비교", "연도별 추이", "목표 달성률"
    ])

# 기본 현황
    with tab1:
        st.subheader("기본 현황")
        brand = st.selectbox("브랜드 선택", df["브랜드"].unique())
        year = st.selectbox("연도 선택", list(range(2025, 2015, -1)), index=1)
        factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].unique())
        month_cols = [col for col in df.columns if str(col).startswith(str(year))]

        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        df_melted = filtered.melt(id_vars=["차종"], value_vars=month_cols, var_name="월", value_name="생산량")
        df_melted = df_melted[df_melted["생산량"] > 0]

        if df_melted.empty:
            st.warning("데이터가 없습니다.")
        else:
            # 추가 정보 계산
            total_prod = df_melted["생산량"].sum()
            avg_prod = df_melted["생산량"].mean()
            model_count = df_melted["차종"].nunique()

        if df_melted.empty:
            st.warning("데이터가 없습니다.")

        else:
            # 라인차트 애니메이션 (차종별 월별 변화)
            st.markdown("#### 월별 차종 생산 추이 (라인차트)")
            fig_line = px.line(
                df_melted,
                x="차종",
                y="생산량",
                animation_frame="월",
                color="차종",
                markers=True,
                title=f"{year}년 {brand} - {factory} 월별 차종 생산 추이",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_line.update_layout(
                xaxis_title="차종",
                yaxis_title="생산량",
                height=500
            )
            st.plotly_chart(fig_line, use_container_width=True)

            # 박스플롯 애니메이션
            st.markdown("#### 생산량 분포 (애니메이션 박스플롯)")
            fig_box = px.box(
                df_melted,
                x="차종",
                y="생산량",
                color="차종",
                animation_frame="월",
                title=f"{year}년 {brand} - {factory} 월별 생산량 분포",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_box.update_layout(
                xaxis_title="차종",
                yaxis_title="생산량",
                height=500
            )
            st.plotly_chart(fig_box, use_container_width=True)
            # 추가 정보 표시
            col1, col2 = st.columns(2)
            col1.info(f"**{year}년 {brand} {factory} 총 생산량**\n\n{total_prod:,.0f}대")
            col2.info(f"**월평균 생산량**\n\n{avg_prod:,.0f}대")
                    


    # 공장별 비교
    with tab2:
        st.subheader("공장별 생산량 비교")
        brand = st.selectbox("브랜드", df["브랜드"].unique(), key="brand_tab2")
        year = st.selectbox("연도", list(range(2025, 2015, -1)), index=1)
        month_cols = [col for col in df.columns if str(col).startswith(str(year))]

        subset = df[df["브랜드"] == brand]
        melted = subset.melt(id_vars=["공장명(국가)"], value_vars=month_cols, var_name="월", value_name="생산량")
        factory_totals = melted.groupby("공장명(국가)")["생산량"].sum().reset_index()

        fig = px.bar(
            melted,
            x="공장명(국가)", y="생산량",
            color="공장명(국가)",
            animation_frame="월",
            title=f"{year}년 {brand} 공장별 월별 생산량",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
        # 추가 정보 표시
        col1, col2 = st.columns(2)
        col1.info(f"**{year}년 {brand} 총 생산량**\n\n{melted['생산량'].sum():,.0f}대")
        col2.info(f"**공장 수**\n\n{len(factory_totals)}개")

    # 연도별 추이
    with tab3:
        st.subheader("연도별 생산 추이")

        brand = st.selectbox("브랜드 선택", df["브랜드"].unique(), key="brand_tab3")
        factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].unique(), key="factory_tab3")
        df_target = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        year_month_totals = []
        for y in sorted({c[:4] for c in df.columns if re.match(r"\d{4}-\d{2}", c)}):
            for m in range(1, 13):
                col = f"{y}-{m:02d}"
                if col in df.columns:
                    total = df_target[col].sum()
                    year_month_totals.append({"연도": y, "월": m, "총생산": total})

        df_year_month = pd.DataFrame(year_month_totals)
        
        # 추가 정보 계산
        annual_totals = df_year_month.groupby("연도")["총생산"].sum().reset_index()

        year_month_totals = []
        for y in sorted({c[:4] for c in df.columns if re.match(r"\d{4}-\d{2}", c)}):
            for m in range(1, 13):
                col = f"{y}-{m:02d}"
                if col in df.columns:
                    total = df_target[col].sum()
                    year_month_totals.append({"연도": y, "월": m, "총생산": total})

        df_year_month = pd.DataFrame(year_month_totals)
        
        fig_animated = px.scatter(df_year_month, x="연도", y="총생산", 
                                size="총생산", color="총생산",
                                animation_frame="월", animation_group="연도",
                                range_y=[0, df_year_month["총생산"].max() * 1.1],
                                title=f"{brand} - {factory} 연도별 생산 추이 (월별 애니메이션)")
        
        fig_animated.update_traces(marker=dict(sizemin=5, sizeref=2.*df_year_month["총생산"].max()/(40.**2)))        

        st.plotly_chart(fig_animated, use_container_width=True)
        # 추가 정보 표시
        col1, col2 = st.columns(2)
        col1.info(f"**전체 기간 총 생산량**\n\n{df_year_month['총생산'].sum():,.0f}대")
        col2.info(f"**연평균 생산량**\n\n{df_year_month.groupby('연도')['총생산'].sum().mean():,.0f}대")


    # 목표 달성률
    with tab4:
        st.subheader("목표 생산 달성률")
        brand = st.selectbox("브랜드", df["브랜드"].unique(), key="brand_tab4")
        year = st.selectbox("연도", list(range(2025, 2015, -1)), index=1, key="year_tab4")
        factory = st.selectbox("공장", df[df["브랜드"] == brand]["공장명(국가)"].unique(), key="factory_tab4")
        goal = st.number_input("목표 생산량 (대)", min_value=100000, step=100000, value=500000)

        month_cols = [col for col in df.columns if str(col).startswith(str(year))]
        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        actual = filtered[month_cols].sum(numeric_only=True).sum()
        rate = round((actual / goal) * 100, 2) if goal > 0 else 0


        # 게이지 차트 생성
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rate,
            title={'text': f"{year}년 목표 달성률"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#6A5ACD"},  # 바늘 색상
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': "#FFCCCC"},
                    {'range': [50, 75], 'color': "#D8BFD8"},
                    {'range': [75, 100], 'color': "#9370DB"}
                ],
                'threshold': {
                    'line': {'color': "purple", 'width': 4},
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
        col1, col2 = st.columns(2)
        col1.info(f"**{year}년 {brand} {factory} 생산량**\n\n{actual:,.0f}대")
        col2.info(f"**목표 대비 달성률**\n\n{rate}% (목표: {goal:,.0f}대)")
