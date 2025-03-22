# core/i18n.py
# ----------------------------
# 다국어 번역 매핑 및 변환 함수
# ----------------------------

def get_text(key: str, lang: str = "ko") -> str:
    translations = {
        "설정": {"ko": "설정", "en": "Settings", "ja": "設定"},
        "테마 선택": {"ko": "테마 선택", "en": "Select Theme", "ja": "テーマ選択"},
        "시스템 관리자 이메일": {"ko": "시스템 관리자 이메일", "en": "Admin Email", "ja": "管理者メール"},
        "판매 관리 모듈 사용": {"ko": "판매 관리 모듈 사용", "en": "Enable Sales Module", "ja": "販売モジュールを有効化"},
        "생산 관리 모듈 사용": {"ko": "생산 관리 모듈 사용", "en": "Enable Production Module", "ja": "生産モジュールを有効化"},
        "재고 관리 모듈 사용": {"ko": "재고 관리 모듈 사용", "en": "Enable Inventory Module", "ja": "在庫モジュールを有効化"},
        "수출 관리 모듈 사용": {"ko": "수출 관리 모듈 사용", "en": "Enable Export Module", "ja": "輸出モジュールを有効化"},
        "AI 추천 시스템 활성화": {"ko": "AI 추천 시스템 활성화", "en": "Enable AI Recommendation", "ja": "AI推薦を有効化"},
        "저장": {"ko": "저장", "en": "Save", "ja": "保存"},
        "언어 선택": {"ko": "언어 선택", "en": "Select Language", "ja": "言語を選択"},
    }
    return translations.get(key, {}).get(lang, key)

# 사용 예시:
# get_text("설정", lang="en") -> "Settings"
# get_text("설정", lang="ja") -> "設定"
