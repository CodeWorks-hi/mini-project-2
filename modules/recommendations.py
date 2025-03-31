import streamlit as st
import re
import requests
from huggingface_hub import InferenceClient
from bs4 import BeautifulSoup
import json

TEXT_MODEL_ID = "google/gemma-2-9b-it"

def fetch_latest_news(keyword="현대자동차", count=5):
    try:
        search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        news_elements = soup.select('.news_area')
        
        for i, item in enumerate(news_elements):
            if i >= count:
                break
                
            title_element = item.select_one('.news_tit')
            title = title_element.text if title_element else "제목 없음"
            link = title_element['href'] if title_element else ""
            
            summary_element = item.select_one('.dsc_wrap')
            summary = summary_element.text.strip() if summary_element else "요약 없음"
            
            date_element = item.select_one('.info_group span.info')
            date = date_element.text if date_element else "날짜 없음"
            
            news_items.append({
                'title': title,
                'link': link,
                'description': summary,
                'pubDate': date
            })
        
        st.session_state.latest_news = news_items
        return news_items
        
    except Exception as e:
        st.error(f"뉴스 가져오기 오류: {e}")
        return []

def get_huggingface_token(model_type):
    tokens = {"gemma": st.secrets.get("HUGGINGFACE_API_TOKEN_GEMMA")}
    return tokens.get(model_type)

def clean_input(text: str) -> str:
    return re.sub(r"(해줘|알려줘|설명해 줘|말해 줘)", "", text).strip()

def clean_html_tags(text):
    return re.sub(r'<[^>]+>', '', text)

def remove_unwanted_phrases(text: str) -> str:
    """
    생성된 결과 텍스트에서 특정 문구(예: '[기타]', '위 내용은 질문에 대한', 
    '보고서 작성을 위해 필요한 정보는 무엇인지요?' 등)를 포함한 줄을 제거
    """
    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        if "[기타]" in line:
            continue
        if "위 내용은 질문에 대한" in line:
            continue
        # 추가: 보고서 작성을 위한 문구 제거
        if "보고서 작성을 위해 필요한 정보는 무엇인지요?" in line:
            continue
        
        filtered_lines.append(line)
    
    return "\n".join(filtered_lines)

def format_news_for_prompt(news_items):
    if not news_items:
        return "최신 뉴스 데이터가 없습니다."
    
    formatted_news = "## 최신 자동차 산업 뉴스\n\n"
    for i, item in enumerate(news_items[:5], 1):
        formatted_news += f"{i}. {item['title']} ({item['pubDate']})\n"
        formatted_news += f"   요약: {item['description'][:100]}...\n\n"
    
    return formatted_news

def format_predictions_for_api(predictions):
    if not predictions:
        return {}
        
    pred_type = predictions.get('type', '')
    
    if pred_type == 'region':
        region_name = predictions.get('name', '지역 정보 없음')
        forecast = predictions.get('forecast', {})
        
        result = f"## {region_name} 지역 수출량 예측\n\n"
        result += "| 연도 | 월 | 예측 수출량 |\n|-----|-----|-----|\n"
        
        years = forecast.get('연도', {})
        months = forecast.get('월', {})
        exports = forecast.get('예측 수출량', {})
        
        if years and months and exports:
            for i in range(len(years)):
                result += f"| {years.get(str(i), '')} | {months.get(str(i), '')} | {exports.get(str(i), '')} |\n"
        
        return result
    
    elif pred_type == 'car':
        car_name = predictions.get('name', '차종 정보 없음')
        forecast = predictions.get('forecast', {})
        
        result = f"## {car_name} 차종 판매량 예측\n\n"
        result += "| 연도 | 월 | 예측 판매량 |\n|-----|-----|-----|\n"
        
        years = forecast.get('연도', {})
        months = forecast.get('월', {})
        sales = forecast.get('예측 판매량', {})
        
        if years and months and sales:
            for i in range(len(years)):
                result += f"| {years.get(str(i), '')} | {months.get(str(i), '')} | {sales.get(str(i), '')} |\n"
        
        return result
    
    elif pred_type == 'plant':
        plant_name = predictions.get('name', '공장 정보 없음')
        forecast = predictions.get('forecast', {})
        
        result = f"## {plant_name} 공장 생산량 예측\n\n"
        result += "| 연도 | 월 | 예측 생산량 |\n|-----|-----|-----|\n"
        
        years = forecast.get('연도', {})
        months = forecast.get('월', {})
        production = forecast.get('예측 판매량', {})
        
        if years and months and production:
            for i in range(len(years)):
                result += f"| {years.get(str(i), '')} | {months.get(str(i), '')} | {production.get(str(i), '')} |\n"
        
        return result
    
    return str(predictions)

def generate_text_via_api(prompt: str, predictions: dict, news_items: list, model_name: str = TEXT_MODEL_ID) -> str:
    token = get_huggingface_token("gemma")
    if not token:
        st.error("Hugging Face API 토큰이 없습니다.")
        return ""

    predictions_formatted = format_predictions_for_api(predictions)
    news_text = format_news_for_prompt(news_items)
    
    system_prompt = """
    [시스템 지시사항]
    ### 1. 분석 요구사항
    - 현대/기아 글로벌 판매 전략 분석
    - 예측 데이터와 최신 뉴스를 종합적으로 고려한 분석
    - 지역별(북미, 유럽, 아시아) 판매 전략 구분 설명
    - 환율 변동이 수출 전략에 미치는 영향 분석
    - 경제 상황에 따른 긍정적/부정적 요인 구분
    - 3가지 시나리오(낙관/중립/비관)로 판매량 예측

    ### 2. 출력 형식
    ## 2025 현대/기아 글로벌 시장 전망 보고서
    | 구분 | 2024 | 2025예상 | 증감률 |
    |------|------|----------|--------|
    | 글로벌 판매량 | X만 대 | Y만 대 | Z% |
    | 주요 시장 점유율 | A% | B% | C%p |

    - 주요 전략:
    - 리스크 요인:
    """

    full_prompt = f"{system_prompt}\n\n[예측 데이터]\n{predictions_formatted}\n\n[최신 뉴스]\n{news_text}\n\n[사용자 질문]\n{prompt}"
    
    try:
        client = InferenceClient(model=model_name, token=token)
        response = client.text_generation(
            prompt=f"다음 요청에 맞는 분석을 전문가처럼 1000자 내외로 요약해줘:\n{full_prompt}",
            max_new_tokens=1000,
            temperature=0.7
        )
        return response
    except Exception as e:
        st.error(f"텍스트 생성 오류: {e}")
        return ""


def recommendations_ui():
    st.title("AI 기반 시장 예측 및 분석")
    st.markdown("""
    - 예측 데이터와 최신 뉴스를 종합한 심층 분석 제공
    - 최신 AI 기술을 활용한 시장 동향 예측
    - 데이터 기반의 객관적이고 통찰력 있는 결과 도출
    """)

    if 'predictions' not in st.session_state:
        st.warning("먼저 '예측 시스템' 탭에서 예측을 실행해주세요.")
        return

    # 1) 예측 결과 (LSTM 기반)
    with st.expander("예측 결과 표 (LSTM 기반)", expanded=False):
        # (디버그용) 원본 출력
        st.write(st.session_state.predictions)

        # 2) 예: format_predictions_for_api()를 통해 HTML 또는 Markdown을 생성했다고 가정
        # 여기서는 간단히 JSON을 예쁘게 출력하는 예시
        # 필요하다면 format_predictions_for_api()로 표 형식 가공 가능
        predictions_str = json.dumps(st.session_state.predictions, ensure_ascii=False, indent=2)

        # 3) 최종 HTML 블록
        st.markdown("### 형식 변환된 예측 데이터")
        st.markdown(
            f"""
            <div style="background-color: #f8f9fa; 
                        padding: 15px; 
                        border-radius: 8px; 
                        margin-bottom: 10px; 
                        border-left: 4px solid #4285f4;">
                <h4 style="margin-top: 0; color: #333;">예측 데이터</h4>
                <pre style="color: #555; white-space: pre-wrap;">{predictions_str}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 이후 필요하다면 추가 UI, 예: 뉴스 표시, 추가 분석 폼 등
    # 뉴스가 없으면 가져오기
    if 'latest_news' not in st.session_state:
        with st.spinner("최신 뉴스를 가져오는 중..."):
            news_items = fetch_latest_news()
            if news_items:
                st.session_state.latest_news = news_items
            else:
                st.error("뉴스를 가져오지 못했습니다.")
                return
    # 최신 뉴스 표시
    with st.expander(" 분석에 사용된 최신 뉴스"):
        for i, news in enumerate(st.session_state.latest_news[:5], 1):
            title = clean_html_tags(news['title'])
            description = clean_html_tags(news['description'])
            
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #4285f4;">
                    <h4 style="margin-top: 0; color: #333;">{i}. {title}</h4>
                    <p style="color: #555;">{description[:150]}...</p>
                    <p style="color: #888; font-size: 0.8em;">{news.get('pubDate', '')}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

    # 첫 번째 폼 (키: analyze_form)
    with st.form("analyze_form"):
        user_input = st.text_area("예측 및 분석 입력", placeholder="예: 2025년 미국 수출 예측해줘")
        submitted = st.form_submit_button("예측 및 분석 실행")
    
    if submitted:
        with st.spinner("시장 예측 및 분석 중..."):
            cleaned = clean_input(user_input)
            raw_result_txt = generate_text_via_api(cleaned, st.session_state.predictions, st.session_state.latest_news)
            
            # 후처리: 원치 않는 문구 제거
            final_result_txt = remove_unwanted_phrases(raw_result_txt)
            
            st.session_state.analysis_result = final_result_txt
            st.markdown(f"### 종합 예측 및 분석 결과\n{final_result_txt}")


    # ---- 중복 폼 제거 또는 키 변경 ----
    #
    # 아래와 같은 두 번째 폼이 중복되어 있다면, 키를 "analyze_form2"처럼 바꾸거나
    # 폼이 실제로 필요 없다면 제거해야 합니다.
    #
    # [예시] 키를 변경한 폼
    #
    # with st.form("analyze_form2"):
    #     user_input2 = st.text_area("추가 분석 입력", placeholder="예: 중동 시장 진출 전략 알려줘")
    #     submitted2 = st.form_submit_button("추가 분석 실행")
    # 
    # if submitted2:
    #     with st.spinner("추가 분석 중..."):
    #         cleaned2 = clean_input(user_input2)
    #         result_txt2 = generate_text_via_api(cleaned2, st.session_state.predictions, st.session_state.latest_news)
    #         st.markdown(f"### 추가 분석 결과\n{result_txt2}")
