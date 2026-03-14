import streamlit as st
import random
import time
from PIL import Image
import easyocr
import numpy as np

# --- 앱 설정 ---
st.set_page_config(page_title="똑똑 유아식 매니저", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 60px; font-size: 18px !important; font-weight: bold; border-radius: 12px; margin-bottom: 10px; }
    .recipe-card { padding: 15px; border-radius: 10px; background-color: #fef9e7; margin-bottom: 15px; border-left: 8px solid #ffcc00; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }
    .storage-card { padding: 15px; border: 1px solid #eee; border-radius: 10px; margin-bottom: 10px; background: white; }
    .meal-title { color: #d35400; font-weight: bold; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 저장소 ---
if 'recipe_db' not in st.session_state:
    st.session_state.recipe_db = [
        {"title": "한우 채소 팝콘", "ingredients": "소고기 다짐육 30g, 전분 1, 양파 10g", "method": "1. 재료 섞기 2. 에어프라이어 180도 10분", "tag": "소고기"},
        {"title": "닭안심 고구마 매쉬", "ingredients": "닭안심 30g, 고구마 1개", "method": "1. 찌기 2. 으깨기", "tag": "단백질"},
        {"title": "대구살 채소 죽", "ingredients": "대구살 30g, 쌀가루, 애호박", "method": "1. 끓이기 2. 뜸들이기", "tag": "생선"}
    ]
if 'page' not in st.session_state: st.session_state.page = "main"

# --- OCR 분석 함수 ---
@st.cache_resource
def get_reader():
    return easyocr.Reader(['ko', 'en'])

# --- [페이지 1] 메인 화면 ---
if st.session_state.page == "main":
    st.title("👶 우리 아이 맞춤 식단")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 레시피 등록"):
            st.session_state.page = "add"
            st.rerun()
    with col2:
        if st.button("📂 레시피 창고"):
            st.session_state.page = "storage"
            st.rerun()
            
    if st.button("📅 오늘 식단 짜기"):
        st.session_state.page = "plan_1"
        st.rerun()
    if st.button("🗓️ 3일치 식단 짜기"):
        st.session_state.page = "plan_3"
        st.rerun()

# --- [페이지 2] 레시피 등록 (요약 기능 포함) ---
elif st.session_state.page == "add":
    st.header("📝 레시피 요약 등록")
    img_file = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
    
    if img_file:
        image = Image.open(img_file)
        st.image(image, caption="분석용 사진", use_container_width=True)
        
        if st.button("🔍 AI 레시피 요약 추출"):
            with st.spinner("글자를 읽고 요약 양식을 만드는 중..."):
                reader = get_reader()
                result = reader.readtext(np.array(image), detail=0)
                full_text = " ".join(result)
                
                # 추출된 텍스트를 기반으로 입력창을 미리 채워줌
                st.session_state.temp_title = full_text[:10]
                st.session_state.temp_ing = full_text
                st.session_state.temp_method = "사진 내용을 참고하여 적어주세요."
                st.success("추출 완료! 아래 양식에 맞춰 내용을 다듬어주세요.")

    # 사용자가 보기 편하게 세분화된 입력창
    title = st.text_input("🍴 메뉴 이름", value=st.session_state.get('temp_title', ''))
    ing = st.text_area("🛒 재료 (예: 소고기 30g, 당근 10g...)", value=st.session_state.get('temp_ing', ''))
    method = st.text_area("👨‍🍳 요리 방법 (순서대로)", value=st.session_state.get('temp_method', ''))
    tag = st.selectbox("핵심 분류", ["소고기", "단백질", "채소", "기타"])
    
    if st.button("✅ 레시피 창고 저장"):
        st.session_state.recipe_db.append({"title": title, "ingredients": ing, "method": method, "tag": tag})
        st.success("저장되었습니다!")
        time.sleep(1)
        st.session_state.page = "main"
        st.rerun()

    if st.button("🔙 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

# --- [페이지 3] 식단 생성 로직 (중복 방지 & 소고기 필수) ---
elif st.session_state.page in ["plan_1", "plan_3"]:
    days = 1 if st.session_state.page == "plan_1" else 3
    st.header(f"🗓️ {days}일 영양 식단")
    
    for i in range(days):
        # 1. 소고기 메뉴 하나 필수로 뽑기 (하루 30g 보충)
        beef_list = [r for r in st.session_state.recipe_db if r['tag'] == "소고기"]
        others = [r for r in st.session_state.recipe_db if r['tag'] != "소고기"]
        
        if not beef_list:
            st.warning("⚠️ 창고에 소고기 레시피가 없어요! 소고기 메뉴를 등록해주세요.")
            day_beef = {"title": "소고기 메뉴 없음", "ingredients": "-", "method": "-"}
        else:
            day_beef = random.choice(beef_list)
            
        # 2. 재료가 중복되지 않게 나머지 메뉴 구성
        remaining = random.sample(others, min(len(others), 2)) if len(others) >= 2 else others
        
        st.markdown(f"""
        <div class="recipe-card">
            <h3 style='margin-top:0;'>Day {i+1}</h3>
            <p><span class="meal-title">🌅 아침:</span> {remaining[0]['title'] if len(remaining)>0 else '메뉴 부족'}</p>
            <p><span class="meal-title">☀️ 점심 (철분필수):</span> {day_beef['title']} (소고기 30g 포함)</p>
            <p><span class="meal-title">🌙 저녁:</span> {remaining[1]['title'] if len(remaining)>1 else '메뉴 부족'}</p>
            <hr>
            <small><b>[오늘의 요리팁]</b><br>{day_beef['title']}: {day_beef['method']}</small>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("🔙 홈으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

# --- [페이지 4] 창고 보기 ---
elif st.session_state.page == "storage":
    st.header("📂 내 레시피 창고")
    for idx, r in enumerate(st.session_state.recipe_db):
        with st.expander(f"{r['title']} (#{r['tag']})"):
            st.write(f"**재료:** {r['ingredients']}")
            st.write(f"**요리방법:** {r['method']}")
            if st.button(f"🗑️ 삭제", key=f"del_{idx}"):
                st.session_state.recipe_db.pop(idx)
                st.rerun()
    if st.button("🔙 메인으로"):
        st.session_state.page = "main"
        st.rerun()
