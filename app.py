import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import pydeck as pdk
import cv2
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px

# 패키지 모듈 불러오기
from src.public_data.mock_loader import load_mock_candidates
from src.public_data.api_adapters import (
    fetch_vworld_land_info,
    fetch_agricultural_zone,
    fetch_soil_suitability,
    fetch_geo_bigdata,
    fetch_youth_policy
)
from src.drone_analysis.rgb_analysis import analyze_rgb_image
from src.drone_analysis.thermal_analysis import analyze_thermal_image
from src.drone_analysis.scoring import calculate_drone_score, calculate_final_score, load_scoring_weights
from src.recommendation.crop_recommender import recommend_crops
from src.utils.io import export_result_json, ensure_output_dir

# ----------------- 페이지 설정 -----------------
st.set_page_config(
    page_title="청년 창농 입지 진단 시스템 MVP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 커스텀 스타일 (CSS) -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E5631;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2D6A4F;
        border-left: 5px solid #40916C;
        padding-left: 10px;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F4F9F4;
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #D8EAD8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 1rem;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #52B788;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1B4332;
    }
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        text-align: center;
    }
    .badge-excellent {
        background-color: #D8F3DC;
        color: #1B4332;
    }
    .badge-good {
        background-color: #FFEFC2;
        color: #8F6B00;
    }
    .badge-poor {
        background-color: #FFE5E5;
        color: #C0392B;
    }
    .result-card {
        background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .result-text {
        font-size: 1.1rem;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- 더미 이미지 생성용 헬퍼 함수 -----------------
def create_default_images_if_not_exists():
    """앱 구동에 필요한 기본 RGB 및 열화상 더미 이미지를 생성합니다."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    sample_dir = os.path.join(data_dir, "sample_images")
    os.makedirs(sample_dir, exist_ok=True)
    
    rgb_path = os.path.join(sample_dir, "sample_rgb.png")
    thermal_path = os.path.join(sample_dir, "sample_thermal.png")
    
    # 1. RGB 더미 이미지 생성 (초록색 밭 영역과 갈색 흙 영역이 섞여 있는 모습)
    if not os.path.exists(rgb_path):
        rgb_img = np.zeros((400, 600, 3), dtype=np.uint8)
        # 잔디밭 배경 (녹색)
        rgb_img[:, :] = [45, 139, 87]
        # 갈색 토양 구역 (농지 정리가 안 된 부분)
        cv2.rectangle(rgb_img, (350, 50), (550, 350), (30, 105, 200), -1)
        # 스마트팜 비닐하우스 모사 (흰색 사각형)
        cv2.rectangle(rgb_img, (50, 80), (180, 220), (220, 220, 220), -1)
        cv2.putText(rgb_img, "Greenhouse Setup", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        cv2.imwrite(rgb_path, rgb_img)
        
    # 2. Thermal 더미 이미지 생성 (온도 분포)
    if not os.path.exists(thermal_path):
        thermal_img = np.zeros((400, 600, 3), dtype=np.uint8)
        # 기본 미지근한 온도 (초록/노랑 스펙트럼)
        for i in range(600):
            val = int(80 + (i / 600) * 100) # 80 ~ 180 밝기
            thermal_img[:, i] = [val, val, val]
            
        # 침수/과습 구역 (어둡고 차가운 물웅덩이 모사, 밝기 30)
        cv2.circle(thermal_img, (200, 250), 70, (30, 30, 30), -1)
        # 비닐하우스 또는 노지 건조 스트레스 구역 (밝고 뜨거운 구역 모사, 밝기 230)
        cv2.circle(thermal_img, (480, 150), 60, (230, 230, 230), -1)
        
        cv2.imwrite(thermal_path, thermal_img)

create_default_images_if_not_exists()

# ----------------- 데이터 로드 -----------------
candidates = load_mock_candidates()
df_candidates = pd.DataFrame(candidates)

# ----------------- 사이드바 네비게이션 -----------------
st.sidebar.image("https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&q=80&w=400", use_container_width=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #1E5631;'>창농 입지 진단 MVP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "메뉴 이동",
    ["1. 프로젝트 개요 & 목적", "2. 1차 농지 후보지 선별 (공공 데이터)", "3. 2차 정밀 분석 (드론 이미지)", "4. 최종 창농 적합도 & 추천"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **해커톤 시연 가이드**\n\n"
    "본 시스템은 공공 데이터 필터링(1차)과 "
    "드론 이미지 기반 공간 분석(2차)을 융합하여 "
    "청년 창업농에게 최적의 입지를 종합 제안하는 "
    "의사결정 지원 MVP 솔루션입니다."
)

# ----------------- 화면 1. 프로젝트 개요 -----------------
if app_mode == "1. 프로젝트 개요 & 목적":
    st.markdown("<div class='main-title'>AI·드론 기반 청년 농업 창업 입지 진단 시스템</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Balanced Regional Development & Youth Agriculture Settlement Solution</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("<div class='section-header'>프로젝트 배경 및 목적</div>", unsafe_allow_html=True)
        st.write(
            "지방 소멸과 청년 인구 유출은 지역 균형 발전의 가장 큰 저해 요소입니다. "
            "정부는 청년 농업인(청년농) 유입 정책을 강력하게 추진하고 있으나, 실제 청년들은 "
            "**'어디에서 어떤 작물을 키워야 성공할지', '해당 토양과 배수 상태는 적합한지'** 등의 현실적인 정보 부족에 직면해 있습니다.\n\n"
            "이에 본 해커톤 MVP는 **공공 농지 빅데이터와 드론 멀티스펙트럼/열화상 공간 정보**, 그리고 **AI 의사결정 모델**을 융합하여, "
            "안전하고 과학적인 창업 입지 진단 정보 및 맞춤형 가이드라인을 제공합니다."
        )
        
        st.markdown("<div class='section-header'>분석 프로세스</div>", unsafe_allow_html=True)
        st.markdown(
            "1. **1차 광역 농지 후보 선별**: 흙토람(토양), 브이월드(지적도), 지오빅데이터(지하수/지질) 등 공공 데이터를 종합 평가하여 1차 후보지 선별\n"
            "2. **2차 미시 드론 영상 분석**: RGB 및 열화상 이미지를 통해 식생 밀도, 유휴 상태, 배수 위험도, 건조 스트레스 구역을 필지 단위로 상세 분석\n"
            "3. **종합 의사결정 및 연계 정책 추천**: 청년농 정착금, 지자체 임대 스마트팜 사업 등 최적의 정부 정책 및 스마트팜 적합 작물 연계 제안"
        )
        
    with col2:
        st.image("https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&q=80&w=800", caption="드론을 활용한 스마트 정밀 농업 분석 모사", use_container_width=True)
        
        st.markdown("<div class='section-header'>시스템 아키텍처</div>", unsafe_allow_html=True)
        st.code(
            "┌────────────────────────┐\n"
            "│   공공 API 데이터 조회 │ 흙토람 / VWorld / 지오빅데이터\n"
            "└───────────┬────────────┘\n"
            "            ▼\n"
            "┌────────────────────────┐\n"
            "│  드론 RGB / 열화상 이미지│ OpenCV 필지 상태 분석\n"
            "└───────────┬────────────┘\n"
            "            ▼\n"
            "┌────────────────────────┐\n"
            "│ AI 규칙 기반 적합도 계산│ 가중합 스코어링 & 등급 산출\n"
            "└───────────┬────────────┘\n"
            "            ▼\n"
            "┌────────────────────────┐\n"
            "│  창농 가이드 & 정책 제안 │ 맞춤 작물 추천 및 PDF/JSON 리포트\n"
            "└────────────────────────┘",
            language="text"
        )

# ----------------- 화면 2. 1차 후보 농지 탐색 -----------------
elif app_mode == "2. 1차 농지 후보지 선별 (공공 데이터)":
    st.markdown("<div class='main-title'>1차 농지 후보지 탐색</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>공공 API 빅데이터 기반 창농 적합성 기초 평가</div>", unsafe_allow_html=True)
    
    # 상단 요약 지표
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>총 분석 후보지</div>"
            f"<div class='metric-value'>{len(df_candidates)} 곳</div></div>",
            unsafe_allow_html=True
        )
    with col2:
        excellent_count = len(df_candidates[df_candidates['public_api_score'] >= 80])
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>우수 등급 (80점 이상)</div>"
            f"<div class='metric-value'>{excellent_count} 곳</div></div>",
            unsafe_allow_html=True
        )
    with col3:
        avg_score = df_candidates['public_api_score'].mean()
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>평균 기초 평가 점수</div>"
            f"<div class='metric-value'>{avg_score:.1f} 점</div></div>",
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>데이터 연동 상태</div>"
            "<div class='metric-value' style='color:#2A9D8F; font-size:1.4rem;'>Mock Mode (정상)</div></div>",
            unsafe_allow_html=True
        )

    # 데이터 프레임 테이블 보여주기
    st.markdown("<div class='section-header'>광역 농지 후보 목록</div>", unsafe_allow_html=True)
    
    # 색상 맵 지정을 위한 스타일링용 컬럼 추가
    def get_color_class(score):
        if score >= 80: return "🟢 우수"
        elif score >= 65: return "🟡 검토가능"
        return "🔴 보완필요"
        
    df_display = df_candidates.copy()
    df_display["평가등급"] = df_display["public_api_score"].apply(get_color_class)
    
    st.dataframe(
        df_display[["candidate_id", "region", "address", "land_type", "area_m2", "public_api_score", "평가등급"]].rename(
            columns={
                "candidate_id": "후보지 ID",
                "region": "행정구역",
                "address": "세부주소",
                "land_type": "지목",
                "area_m2": "면적(㎡)",
                "public_api_score": "공공 평가점수"
            }
        ),
        use_container_width=True
    )
    
    # 맵 & 상세정보 레이아웃
    col_map, col_detail = st.columns([3, 2])
    
    with col_map:
        st.markdown("<div class='section-header'>후보지 위치 분포 지도</div>", unsafe_allow_html=True)
        
        # 지도에 표시할 색상 매핑
        def score_to_color(score):
            if score >= 80:
                return [34, 139, 34, 200]  # Green
            elif score >= 65:
                return [218, 165, 32, 200] # Yellow
            else:
                return [220, 20, 60, 200]   # Red
                
        df_candidates['color'] = df_candidates['public_api_score'].apply(score_to_color)
        
        # Pydeck을 이용한 인터랙티브 지도 시각화
        view_state = pdk.ViewState(
            latitude=df_candidates['lat'].mean(),
            longitude=df_candidates['lng'].mean(),
            zoom=6.5,
            pitch=0
        )
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_candidates,
            get_position="[lng, lat]",
            get_color="color",
            get_radius=8000,
            pickable=True,
            auto_highlight=True
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "ID: {candidate_id}\n주소: {address}\n점수: {public_api_score}"}
        )
        st.pydeck_chart(r)
        st.caption("색상 안내: 초록색(80점 이상 - 우수) / 노란색(65~80점 - 보통) / 빨간색(65점 미만 - 미흡)")

    with col_detail:
        st.markdown("<div class='section-header'>후보지 상세 평가 분석</div>", unsafe_allow_html=True)
        selected_id = st.selectbox(
            "지목 및 상세 정보를 분석할 후보지를 선택하세요.",
            df_candidates['candidate_id'].tolist()
        )
        
        candidate = df_candidates[df_candidates['candidate_id'] == selected_id].iloc[0]
        
        # 상세 데이터 수치 표시
        st.markdown(f"### **{candidate['candidate_id']}** ({candidate['land_type']})")
        st.markdown(f"📍 **주소**: {candidate['address']}")
        st.markdown(f"📐 **면적**: {candidate['area_m2']:,} ㎡")
        
        # 공공데이터 레이더 차트 그리기
        categories = [
            '토양/작물 적성', '농업진흥지역', '실제농경지 여부', 
            '접근성', '배수/경사', '지하수/지질', '청년정책 지원'
        ]
        values = [
            candidate['soil_crop_score'],
            candidate['agricultural_zone_score'],
            candidate['actual_farmland_score'],
            candidate['accessibility_score'],
            candidate['drainage_slope_score'],
            candidate['geo_environment_score'],
            candidate['youth_policy_score']
        ]
        
        # Plotly Radar Chart
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(64, 145, 108, 0.3)',
            line=dict(color='#1B4332', width=2),
            name=candidate['candidate_id']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
            height=280
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ----------------- 화면 3. 2차 드론 이미지 분석 -----------------
elif app_mode == "3. 2차 정밀 분석 (드론 이미지)":
    st.markdown("<div class='main-title'>2차 미시 드론 분석</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>항공 드론 RGB 매핑 및 열화상 온도 편차 분석을 통한 현장 정밀 진단</div>", unsafe_allow_html=True)
    
    # 후보지 선택 상태 동기화
    if 'selected_candidate_id' not in st.session_state:
        st.session_state['selected_candidate_id'] = df_candidates['candidate_id'].iloc[0]
        
    selected_id = st.selectbox(
        "분석을 진행할 농지 후보지를 선택하세요.",
        df_candidates['candidate_id'].tolist(),
        index=df_candidates['candidate_id'].tolist().index(st.session_state['selected_candidate_id'])
    )
    st.session_state['selected_candidate_id'] = selected_id
    candidate = df_candidates[df_candidates['candidate_id'] == selected_id].iloc[0]
    
    st.markdown(f"#### 📍 대상 농지: {candidate['address']} ({candidate['candidate_id']})")
    
    # 이미지 업로드 컨트롤러
    st.markdown("<div class='section-header'>드론 원격 탐사 데이터 업로드</div>", unsafe_allow_html=True)
    col_up1, col_up2 = st.columns(2)
    
    with col_up1:
        rgb_file = st.file_uploader("1. 드론 RGB 공간 정보 이미지 업로드 (PNG, JPG)", type=["png", "jpg", "jpeg"])
    with col_up2:
        thermal_file = st.file_uploader("2. 드론 열화상(Thermal) 이미지 업로드 (PNG, JPG)", type=["png", "jpg", "jpeg"])
        
    # 시연 편의를 위한 샘플 이미지 자동 제공 기능
    use_sample = st.checkbox("샘플 드론 분석 이미지 데이터 사용 (업로드 이미지 없을 때 대체)", value=True)
    
    rgb_img_to_analyze = None
    thermal_img_to_analyze = None
    
    # 이미지 불러오기 로직
    if rgb_file is not None:
        rgb_img_to_analyze = Image.open(rgb_file)
    elif use_sample:
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_images", "sample_rgb.png")
        if os.path.exists(sample_path):
            rgb_img_to_analyze = Image.open(sample_path)
            
    if thermal_file is not None:
        thermal_img_to_analyze = Image.open(thermal_file)
    elif use_sample:
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_images", "sample_thermal.png")
        if os.path.exists(sample_path):
            thermal_img_to_analyze = Image.open(sample_path)

    # 분석 수행
    if rgb_img_to_analyze is not None and thermal_img_to_analyze is not None:
        if st.button("🚀 드론 AI 종합 영상 공간 분석 실행", type="primary", use_container_width=True):
            with st.spinner("드론 고해상도 이미지 및 열정보 매핑 레이어를 병합하여 비정형 토양/식생 속성을 분석하고 있습니다..."):
                # 분석 엔진 실행
                rgb_metrics, rgb_visualized = analyze_rgb_image(rgb_img_to_analyze)
                thermal_metrics, thermal_visualized = analyze_thermal_image(thermal_img_to_analyze)
                
                # 분석 점수 산출
                drone_score, drone_details = calculate_drone_score(rgb_metrics, thermal_metrics)
                
                # 결과 임시 보관 (session_state 활용)
                st.session_state['drone_analysis_done'] = True
                st.session_state['last_candidate_id'] = selected_id
                st.session_state['rgb_metrics'] = rgb_metrics
                st.session_state['thermal_metrics'] = thermal_metrics
                st.session_state['drone_score'] = drone_score
                st.session_state['drone_details'] = drone_details
                
                # 시각화 이미지 RGB 변환 (OpenCV BGR -> RGB)
                st.session_state['rgb_visualized_rgb'] = cv2.cvtColor(rgb_visualized, cv2.COLOR_BGR2RGB)
                st.session_state['thermal_visualized_rgb'] = cv2.cvtColor(thermal_visualized, cv2.COLOR_BGR2RGB)
                
                # 원본 백업
                st.session_state['rgb_original'] = np.array(rgb_img_to_analyze)
                st.session_state['thermal_original'] = np.array(thermal_img_to_analyze)

    # 분석 완료 후 화면 표시
    if st.session_state.get('drone_analysis_done', False) and st.session_state.get('last_candidate_id', '') == selected_id:
        
        st.success("✅ 드론 이미지 공간 격자 데이터 분석 완료!")
        
        # 점수 표시 리포트
        score_col1, score_col2 = st.columns([1, 2])
        
        with score_col1:
            st.markdown(
                f"<div class='metric-card'><div class='metric-title'>2차 드론 종합 평가 점수</div>"
                f"<div class='metric-value'>{st.session_state['drone_score']:.1f} 점</div></div>",
                unsafe_allow_html=True
            )
            
            # 레이아웃 카드 형태의 세부 점수
            st.markdown("##### 🔍 드론 분석 정밀 평가 정보")
            details = st.session_state['drone_details']
            st.markdown(f"🌿 **식생 건강도**: {details['vegetation_health_score']}점")
            st.markdown(f"💧 **수분 균형도**: {details['moisture_balance_score']}점")
            st.markdown(f"🚜 **농지 정리상태**: {details['field_condition_score']}점")
            st.markdown(f"⚠️ **배수 관리점수 (안전도)**: {details['drainage_risk_reverse_score']}점")
            st.markdown(f"🏗️ **시설 설치 가능성**: {details['facility_installation_score']}점")
            st.markdown(f"🧹 **관리 난이도 점수**: {details['management_difficulty_score']}점 (낮을수록 우수)")
            
        with score_col2:
            # 점수 바 차트
            details = st.session_state['drone_details']
            chart_data = pd.DataFrame({
                "평가 항목": ["식생 건강도", "수분 균형도", "농지 정리상태", "배수 안전도", "시설 설치용이성", "관리 용이성"],
                "점수": [
                    details['vegetation_health_score'],
                    details['moisture_balance_score'],
                    details['field_condition_score'],
                    details['drainage_risk_reverse_score'],
                    details['facility_installation_score'],
                    details['management_difficulty_reverse_score']
                ]
            })
            fig = px.bar(
                chart_data, x="점수", y="평가 항목", orientation="h",
                color="점수", color_continuous_scale="Viridis",
                range_x=[0, 100]
            )
            fig.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
        # 이미지 시각화 결과 보여주기
        st.markdown("<div class='section-header'>공간 원격 탐사 매핑 시각화 (원본 vs AI 오버레이 분석)</div>", unsafe_allow_html=True)
        
        tab_rgb, tab_thermal = st.tabs(["🌱 RGB 이미지 식생/토양 분석", "🔥 열화상(Thermal) 수분/온도 분석"])
        
        with tab_rgb:
            col_rgb_orig, col_rgb_analyzed = st.columns(2)
            with col_rgb_orig:
                st.image(st.session_state['rgb_original'], caption="드론 RGB 원본 고화질 공간 정보", use_container_width=True)
            with col_rgb_analyzed:
                st.image(st.session_state['rgb_visualized_rgb'], caption="식생 구역(초록색) 및 토양/나지(주황색) AI 구획 분석 오버레이", use_container_width=True)
                
        with tab_thermal:
            col_th_orig, col_th_analyzed = st.columns(2)
            with col_th_orig:
                st.image(st.session_state['thermal_original'], caption="드론 열화상 흑백(Grayscale) 원본 이미지", use_container_width=True)
            with col_th_analyzed:
                st.image(st.session_state['thermal_visualized_rgb'], caption="지표면 온도 분포 맵 (파란색: 과습 및 침수 구역 / 빨간색: 건조 스트레스 구역)", use_container_width=True)
    else:
        st.warning("분석 버튼을 클릭해 드론 영상 정밀 공간 분석을 실행해 주세요.")

# ----------------- 화면 4. 최종 창농 적합도 & 추천 -----------------
elif app_mode == "4. 최종 창농 적합도 & 추천":
    st.markdown("<div class='main-title'>최종 창농 적합도 및 추천 결과</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>공공 데이터와 드론 정밀 분석을 종합한 청년 창농 입지 진단 리포트</div>", unsafe_allow_html=True)
    
    # 2차 분석 결과 검증
    if not st.session_state.get('drone_analysis_done', False):
        st.warning("⚠️ 3단계 메뉴에서 '드론 AI 종합 영상 공간 분석'을 완료하고 이 단계로 이동해야 세부 추천 리포트 조회가 가능합니다.")
        # 만약 분석이 안 되어 있을 경우, 사용자 편의를 위해 디폴트 데이터 자동 셋업
        if st.checkbox("테스트 시뮬레이션용 더미 분석 결과 채우기", value=True):
            # 임시 데이터 로드
            candidate = df_candidates[df_candidates['candidate_id'] == st.session_state.get('selected_candidate_id', 'FARM-001')].iloc[0]
            
            # sample image 로드
            sample_path_rgb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_images", "sample_rgb.png")
            sample_path_th = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_images", "sample_thermal.png")
            
            rgb_img = Image.open(sample_path_rgb)
            th_img = Image.open(sample_path_th)
            
            rgb_metrics, rgb_visualized = analyze_rgb_image(rgb_img)
            thermal_metrics, thermal_visualized = analyze_thermal_image(th_img)
            
            drone_score, drone_details = calculate_drone_score(rgb_metrics, thermal_metrics)
            
            st.session_state['drone_analysis_done'] = True
            st.session_state['last_candidate_id'] = candidate['candidate_id']
            st.session_state['rgb_metrics'] = rgb_metrics
            st.session_state['thermal_metrics'] = thermal_metrics
            st.session_state['drone_score'] = drone_score
            st.session_state['drone_details'] = drone_details
            st.session_state['rgb_visualized_rgb'] = cv2.cvtColor(rgb_visualized, cv2.COLOR_BGR2RGB)
            st.session_state['thermal_visualized_rgb'] = cv2.cvtColor(thermal_visualized, cv2.COLOR_BGR2RGB)
            st.session_state['rgb_original'] = np.array(rgb_img)
            st.session_state['thermal_original'] = np.array(th_img)
            
            st.rerun()

    if st.session_state.get('drone_analysis_done', False):
        selected_id = st.session_state['last_candidate_id']
        candidate = df_candidates[df_candidates['candidate_id'] == selected_id].iloc[0]
        
        # 최종 종합 점수 산출
        public_score = candidate['public_api_score']
        drone_score = st.session_state['drone_score']
        youth_policy_score = candidate['youth_policy_score']
        
        final_score, suitability_grade = calculate_final_score(public_score, drone_score, youth_policy_score)
        
        # 추천 내용 계산
        recommended_crops, risks, policy_recommendations, analysis_summary = recommend_crops(
            candidate.to_dict(),
            st.session_state['drone_details']
        )
        
        # 1. 상단 종합 요약 결과 카드
        st.markdown(
            f"<div class='result-card'>"
            f"<h3>🎯 {candidate['candidate_id']} 입지 진단 결과: [{suitability_grade}]</h3>"
            f"<p class='result-text'>{analysis_summary}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 2. 종합 점수 지표들
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        # 등급 배지 지정
        if suitability_grade == "매우 적합":
            badge_html = "<span class='badge badge-excellent'>매우 적합</span>"
        elif suitability_grade == "적합":
            badge_html = "<span class='badge badge-excellent'>적합</span>"
        elif suitability_grade == "조건부 적합":
            badge_html = "<span class='badge badge-good'>조건부 적합</span>"
        else:
            badge_html = "<span class='badge badge-poor'>개선/보완 필요</span>"
            
        with col_f1:
            st.markdown(
                f"<div class='metric-card'><div class='metric-title'>최종 창농 적합도 점수</div>"
                f"<div class='metric-value' style='color:#1B4332; font-size:2.2rem;'>{final_score} 점</div></div>",
                unsafe_allow_html=True
            )
        with col_f2:
            st.markdown(
                f"<div class='metric-card'><div class='metric-title'>1차 공공 데이터 점수 (50%)</div>"
                f"<div class='metric-value'>{public_score:.1f} 점</div></div>",
                unsafe_allow_html=True
            )
        with col_f3:
            st.markdown(
                f"<div class='metric-card'><div class='metric-title'>2차 드론 분석 점수 (35%)</div>"
                f"<div class='metric-value'>{drone_score:.1f} 점</div></div>",
                unsafe_allow_html=True
            )
        with col_f4:
            st.markdown(
                f"<div class='metric-card'><div class='metric-title'>청년농 지원 가산점 (15%)</div>"
                f"<div class='metric-value'>{youth_policy_score:.1f} 점</div></div>",
                unsafe_allow_html=True
            )
            
        # 3. 상세 진단 결과 그리드 (작물추천 / 위험요소 / 정책연계)
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            st.markdown("<div class='section-header'>🌱 추천 재배 작물 및 비즈니스 모델</div>", unsafe_allow_html=True)
            for crop in recommended_crops:
                st.info(f"👉 **{crop}**")
                
            st.markdown("<div class='section-header'>⚠️ 현장 주요 위험 요소 (Risk Factors)</div>", unsafe_allow_html=True)
            for risk in risks:
                st.warning(f"🚨 {risk}")
                
        with col_rec2:
            st.markdown("<div class='section-header'>🏛️ 연계 가능한 공공·지자체 지원 정책</div>", unsafe_allow_html=True)
            for policy in policy_recommendations:
                st.success(f"📌 {policy}")
                
            st.markdown("<div class='section-header'>📈 종합 가중치 분배 현황</div>", unsafe_allow_html=True)
            # 가중치 원형 차트 그리기
            weight_labels = ["1차 공공데이터 (50%)", "2차 드론 분석 (35%)", "청년 정책 지원 (15%)"]
            weight_values = [50, 35, 15]
            fig_pie = go.Figure(data=[go.Pie(labels=weight_labels, values=weight_values, hole=.3)])
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=10, b=10),
                height=220,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # 4. JSON 다운로드 기능
        st.markdown("<div class='section-header'>데이터 내보내기 (Export Result)</div>", unsafe_allow_html=True)
        
        # JSON 포맷으로 저장할 딕셔너리 구성
        result_dict = {
            "candidate_id": selected_id,
            "region": candidate['region'],
            "location": {
                "lat": float(candidate['lat']),
                "lng": float(candidate['lng'])
            },
            "area_m2": int(candidate['area_m2']),
            "public_api_score": float(public_score),
            "drone_analysis_score": float(drone_score),
            "final_startup_suitability": float(final_score),
            "suitability_grade": suitability_grade,
            "recommended_crops": recommended_crops,
            "risks": risks,
            "policy_recommendations": policy_recommendations,
            "analysis_summary": analysis_summary,
            "analysis": {
                "public_data": {
                    "soil_crop_score": int(candidate['soil_crop_score']),
                    "agricultural_zone_score": int(candidate['agricultural_zone_score']),
                    "actual_farmland_score": int(candidate['actual_farmland_score']),
                    "accessibility_score": int(candidate['accessibility_score']),
                    "drainage_slope_score": int(candidate['drainage_slope_score']),
                    "geo_environment_score": int(candidate['geo_environment_score']),
                    "youth_policy_score": int(candidate['youth_policy_score'])
                },
                "drone_data": st.session_state['drone_details']
            }
        }
        
        # 파일 저장 및 바이트화
        json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
        
        # 파일로 내부 저장 (outputs/results/)
        local_saved_path = export_result_json(result_dict, selected_id)
        st.caption(f"💾 시스템 로그: 진단 결과가 로컬에 안전하게 영구 저장되었습니다. (`{local_saved_path}`)")
        
        st.download_button(
            label="📥 최종 진단 리포트 JSON 파일 다운로드",
            data=json_str.encode('utf-8'),
            file_name=f"AgriYouth_Diagnosis_Report_{selected_id}.json",
            mime="application/json",
            use_container_width=True
        )
