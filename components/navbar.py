import streamlit as st
from streamlit_option_menu import option_menu

def navbar():
    with st.sidebar:
        selected = option_menu(
            "ERP 메뉴",
            ["홈", "대시보드", "판매 관리", "생산 관리", "재고 관리", "수출 관리", "추천 시스템", "분석 리포트", "설정"],
            icons=["house", "bar-chart", "cart", "tools", "archive", "globe", "lightbulb", "file-text", "gear"],
            menu_icon="menu-button",
            default_index=0
        )
    return selected
