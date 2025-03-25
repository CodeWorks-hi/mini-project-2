import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime

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
        st.error(f"🔒 인증 오류: {e.response.status_code} - API 키를 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"❗ 오류 발생: {str(e)}")
        return None


def export_ui():
    st.title("📤 수출 실적 대시보드")
    st.button("+ 수출 등록")

    # 데이터 로딩
    hyundai = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
    kia = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")
    hyundai["브랜드"] = "현대"
    kia["브랜드"] = "기아"
    df = pd.concat([hyundai, kia], ignore_index=True)

    month_cols = [f"{i}월" for i in range(1, 13)]
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce')

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 기본 현황", "🌍 국가별 비교", "📈 연도별 추이", "🎯 목표 달성률", "🗺️ 수출 지도", "📊 성장률 분석", "💱 실시간 환율"
    ])



    # 실시간 환율 탭
    with tab7:
        st.subheader("💱 실시간 환율 정보")
        
        # 날짜 선택기 추가 (테스트용)
        selected_date = st.date_input("날짜 선택", value=datetime(2025, 3, 24))
        data = fetch_currency_data(selected_date.strftime("%Y-%m-%d"))
        
        if data:
            # 데이터 구조 처리 개선
            processed_data = {
                curr: info["value"] 
                for curr, info in data.items()
                if curr in ['USD', 'EUR', 'CAD', 'JPY', 'GBP', 'CNY']
            }
            
            exchange_df = pd.DataFrame({
                "currency": processed_data.keys(),
                "exchange_rate": processed_data.values()
            })
            
            # 통화 순서 정렬
            currencies_order = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'CAD']
            exchange_df["currency"] = pd.Categorical(
                exchange_df["currency"], 
                categories=currencies_order, 
                ordered=True
            )
            exchange_df.sort_values("currency", inplace=True)
            
            # 데이터 표시
            st.dataframe(
                exchange_df,
                column_config={
                    "currency": st.column_config.TextColumn("통화", width="medium"),
                    "exchange_rate": st.column_config.NumberColumn(
                        "환율 (1KRW 기준)",
                        format="%.4f",
                        help="1원 당 외화 가치"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 시각화 개선
            chart = alt.Chart(exchange_df).mark_bar().encode(
                x=alt.X('currency:N', title='통화', sort=currencies_order),
                y=alt.Y('exchange_rate:Q', title='환율', axis=alt.Axis(format=".4f")),
                color=alt.Color('currency:N', legend=None),
                tooltip=[
                    alt.Tooltip('currency', title='통화'),
                    alt.Tooltip('exchange_rate', title='환율', format=".4f")
                ]
            ).properties(
                title=f"{selected_date} 기준 주요 통화 환율",
                width=600,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)
            
        else:
            st.warning("⚠️ 환율 데이터를 불러올 수 없습니다.")

