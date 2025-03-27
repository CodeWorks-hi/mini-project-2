import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
import plotly.graph_objects as go

def load_data():
    hyundai = pd.read_csv("data/processed/hyundai-by-plant.csv")
    kia = pd.read_csv("data/processed/kia-by-plant.csv")
    
    if "차종" not in hyundai.columns:
        hyundai["차종"] = "기타"
    if "차종" not in kia.columns:
        kia["차종"] = "기타"
    
    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"
    
    df = pd.concat([hyundai, kia], ignore_index=True)
    
    # 데이터가 0인 경우 '기타'로 처리
    numeric_cols = df.select_dtypes(include=['number']).columns
    df.loc[:, "차종"] = df.apply(lambda row: "기타" if row[numeric_cols].sum() == 0 else row["차종"], axis=1)
    
    return df


def production_ui():
    df = load_data()
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 기본 현황", "🏢 공장별 비교", "📈 연도별 추이", "🎯 목표 달성률"
    ])
    
    with tab1:
        st.subheader("📊 기본 현황")
        
        brand = st.selectbox("브랜드 선택", df["브랜드"].unique(), key="brand_tab1")
        year = st.selectbox("연도 선택", sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True), key="year_tab1")
        factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].unique(), key="factory_tab1")
        
        month_cols = [col for col in df.columns if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)]
        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        
        if not filtered.empty:
            df_melted = filtered.melt(id_vars=["차종"], value_vars=month_cols, var_name="월", value_name="생산량")
            df_melted = df_melted[df_melted["생산량"] > 0]  # 0 제외
            
            # 차종별 생산량 계산
            model_production = filtered.groupby("차종")[month_cols].sum().sum(axis=1)
            model_production = model_production[model_production > 0]  # 0 제외

            df_hist = model_production.reset_index()
            df_hist.columns = ["차종", "생산량"]

            # 히스토그램 스타일의 막대 차트
            fig_hist = px.histogram(
                df_hist,
                x="차종",
                y="생산량",
                color="차종",
                text_auto=True,
                title=f"{year}년 {brand} - {factory} 차종별 생산량 분포",
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig_hist.update_layout(
                bargap=0.3,
                xaxis_title="차종",
                yaxis_title="총 생산량",
                height=500
            )

            st.plotly_chart(fig_hist, use_container_width=True)

            #2. 히스토그램 + 박스 플롯 조합
            col1, col2 = st.columns(2)
            
            with col1:
                # 히스토그램 (Altair)
                hist = alt.Chart(df_melted).mark_bar().encode(
                    x=alt.X("생산량:Q", bin=alt.Bin(maxbins=30), title="생산량 구간"),
                    y=alt.Y("count()", title="발생 빈도"),
                    color=alt.Color("차종:N", legend=alt.Legend(title="차종"))
                ).properties(
                    title="생산량 분포 차트",
                    width=400,
                    height=300
                )
                st.altair_chart(hist, use_container_width=True)
            
            with col2:
                # 박스 플롯 (Plotly)
                fig_box = px.box(df_melted, 
                                x="차종", 
                                y="생산량",
                                color="차종",
                                title="차종별 생산량 분포")
                fig_box.update_layout(
                    xaxis_title="차종",
                    yaxis_title="생산량",
                    showlegend=False
                )
                st.plotly_chart(fig_box, use_container_width=True)

    
    with tab2:
        st.subheader("🏢 공장별 비교")
        
        brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="brand_tab2")
        year = st.selectbox("연도 선택", sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True), key="year_tab2")
        
        month_cols = [col for col in df.columns if col.startswith(str(year)) and re.match(r"\d{4}-\d{2}", col)]
        df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
        grouped = df[(df["브랜드"] == brand)]
        
        compare_df = grouped.groupby("공장명(국가)")[month_cols].sum(numeric_only=True)
        compare_df["총생산"] = compare_df.sum(axis=1)
        compare_df = compare_df.reset_index()
        
        fig = px.bar(compare_df, 
                    x="공장명(국가)", 
                    y="총생산",
                    title=f"{year}년 {brand} 공장별 총 생산량 비교",
                    labels={'총생산': '총 생산량'},
                    color="공장명(국가)",
                    color_discrete_sequence=px.colors.qualitative.Set2)

        fig.update_layout(
            xaxis_title="공장명(국가)",
            yaxis_title="총 생산량",
            legend_title="공장명(국가)",
            font=dict(size=14),
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickangle=45),
            height=600
        )

        fig.update_traces(texttemplate='%{y}', textposition='outside')

        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📈 연도별 추이")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="brand_tab3")
            factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(), key="factory_tab3")
        
        with col1:
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
                fig = px.line(result_df, x="연도", y="총생산", 
                            title=f"{brand} - {factory} 연도별 총 생산량",
                            labels={"총생산": "총 생산량"},
                            markers=True)

                fig.update_layout(
                    xaxis_title="연도",
                    yaxis_title="총 생산량",
                    font=dict(size=14),
                    plot_bgcolor='rgba(0,0,0,0)',
                    width=700,
                    height=400
                )

                fig.update_traces(line=dict(color='#7E57C2', width=2),
                                marker=dict(size=8, symbol='circle', 
                                            color='#7E57C2',
                                            line=dict(color='#FFFFFF', width=2)))

                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("🎯 목표 달성률")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            brand = st.selectbox("브랜드 선택", df["브랜드"].dropna().unique(), key="brand_tab4")
        with col2:
            year = st.selectbox("연도 선택", sorted({col.split("-")[0] for col in df.columns if re.match(r"\d{4}-\d{2}", col)}, reverse=True), key="year_tab4")
        with col3:
            factory = st.selectbox("공장 선택", df[df["브랜드"] == brand]["공장명(국가)"].dropna().unique(), key="factory_tab4")
        with col4:
            goal = st.number_input("목표 생산량 (대)", min_value=0, step=1000, key="goal_tab4")
        
        month_cols = [col for col in df.columns if col.startswith(year) and re.match(r"\d{4}-\d{2}", col)]
        df[month_cols] = df[month_cols].apply(pd.to_numeric, errors="coerce")
        filtered = df[(df["브랜드"] == brand) & (df["공장명(국가)"] == factory)]
        
        actual = int(filtered[month_cols].sum().sum()) if not filtered.empty else 0
        rate = (actual / goal * 100) if goal > 0 else 0
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=rate,
                title={'text': f"{year}년 {brand} - {factory} 목표 달성률"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "purple"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 75], 'color': "gray"},
                           {'range': [75, 100], 'color': "darkgray"}],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': 90}}
            ))
            fig_gauge.update_layout(height=350)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_d:
            fig_bar = go.Figure(data=[
                go.Bar(name="목표", x=["목표"], y=[goal], marker_color="lightblue"),
                go.Bar(name="실제 생산량", x=["실제"], y=[actual], marker_color="purple")
            ])
            fig_bar.update_layout(
                barmode="group",
                title=f"{year}년 {brand} - {factory} 목표 vs 실제 생산량",
                height=350,
                xaxis_title="구분",
                yaxis_title="수량 (대)",
                legend_title="데이터"
            )
            fig_bar.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

