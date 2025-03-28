# modules/dashboard_news.py

import streamlit as st
import requests
import re
from datetime import datetime

# 🔹 1. HTML 태그 제거 함수
def clean_html(text: str) -> str:
    return re.sub(r"<.*?>", "", text or "")

# 🔹 2. 설명 자르기 함수
def trim_text(text: str, max_length=150) -> str:
    return text if len(text) <= max_length else text[:max_length].rstrip() + "..."

# 🔹 3. 네이버 뉴스 API 조회 함수
def fetch_naver_news(query: str, display: int = 5, sort: str = "date") -> list:
    try:
        client_id = st.secrets["naver"]["client_id"]
        client_secret = st.secrets["naver"]["client_secret"]
    except Exception:
        st.error("네이버 API 키가 누락되었습니다. `.streamlit/secrets.toml` 파일을 확인해주세요.")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    params = {"query": query, "display": display, "sort": sort}
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json().get("items", [])
        else:
            st.error(f"뉴스 검색 실패 (status code: {response.status_code})")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 오류: {e}")
        return []

# 🔹 4. 뉴스 카드 시각화 함수
def render_news_results(news_items: list):
    if not news_items:
        st.warning("뉴스 검색 결과가 없습니다.")
        return

    for news in news_items:
        title = clean_html(news.get("title", "제목 없음")).strip()
        link = news.get("link", "#")
        description = clean_html(news.get("description", "")).strip()
        pub_date = news.get("pubDate", "")

        # 날짜 포맷 정제
        try:
            pub_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
        except Exception:
            pub_date = ""

        description = trim_text(description, max_length=150)

        st.markdown(
            f"""
            <div style="background-color: #f8f8fa; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #ddd;">
                <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 0.4rem;">
                     <a href="{link}" target="_blank" style="text-decoration: none; color: #333;">{title}</a>
                </div>
                <div style="font-size: 0.85rem; color: gray; margin-bottom: 0.6rem;"> {pub_date}</div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #444;">{description}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
