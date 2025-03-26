import os
import streamlit.components.v1 as components

# 개발용 or 배포용 경로 구분
_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "my_component",
        url="http://localhost:5173",  # 개발 서버 주소
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component("my_component", path=build_dir)

# 사용 함수
def my_component(name="사용자"):
    return _component_func(name=name, default="Hello from React!")
