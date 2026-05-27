from typing import Dict, Any, List, Tuple

def recommend_crops(candidate_info: Dict[str, Any], drone_details: Dict[str, Any]) -> Tuple[List[str], List[str], List[str], str]:
    """1차 공공 데이터와 2차 드론 이미지 분석 결과를 분석하여
    추천 작물, 위험요소, 정책 추천 사항 및 요약 분석 문구를 생성합니다.
    
    Args:
        candidate_info (Dict[str, Any]): 후보지 1차 공공데이터 정보
        drone_details (Dict[str, Any]): 2차 드론 분석 세부 점수 정보
        
    Returns:
        Tuple[List[str], List[str], List[str], str]:
            - recommended_crops: 추천 작물 목록
            - risks: 주요 위험 요소
            - policy_recommendations: 추천 정책 사업
            - analysis_summary: 최종 분석 요약 문구
    """
    recommended_crops = []
    risks = []
    policy_recommendations = []
    
    # 1. 추천 작물 로직
    # 조건 A: 시설 설치 점수가 높고 수분 균형이 양호한 경우 -> 스마트팜 기반 고부가가치 작물
    if drone_details.get("facility_installation_score", 0) >= 75 and drone_details.get("moisture_balance_score", 0) >= 70:
        recommended_crops.append("스마트팜 딸기")
        recommended_crops.append("방울토마토")
    
    # 조건 B: 면적이 작고(1500m2 미만) 접근성이 우수한 경우 -> 체험형 또는 로컬푸드
    area = candidate_info.get("area_m2", 0)
    accessibility = candidate_info.get("accessibility_score", 0)
    if area < 2000 and accessibility >= 75:
        recommended_crops.append("체험형 주말 텃밭")
        recommended_crops.append("로컬푸드 재배지(엽채류)")
    
    # 조건 C: 토양 점수가 높고 일반 밭농사에 적합한 경우 -> 일반 고추 또는 노지 작물
    soil_score = candidate_info.get("soil_crop_score", 0)
    if soil_score >= 80:
        if "고추" not in recommended_crops:
            recommended_crops.append("고추")
        if "상추/엽채류" not in recommended_crops:
            recommended_crops.append("상추/엽채류")
            
    # 조건 D: 관리 난이도가 높고 방치 흔적이 있음 -> 청년 실험 농장 (테스트 베드)
    management_difficulty = drone_details.get("management_difficulty_score", 0)
    if management_difficulty >= 40:
        recommended_crops.append("청년 실험 농장 (노지 스마트 농업 실증)")

    # 기본값 채우기 (아무 조건도 만족하지 않는 경우 기본 작물 추천)
    if not recommended_crops:
        recommended_crops = ["상추/엽채류", "고구마/감자 (구황작물)", "로컬푸드 재배지"]

    # 2. 위험요소 식별 로직
    drainage_risk = drone_details.get("drainage_risk_score", 0)
    if drainage_risk >= 35:
        risks.append(f"일부 구역 배수 불량 및 과습 의심 (드론 열화상 저온 영역 {drone_details.get('drainage_risk_score')}% 감지)")
    
    if drainage_risk < 15 and drone_details.get("moisture_balance_score", 0) < 65:
        risks.append("토양 건조 및 용수 부족 가능성 (가뭄 스트레스 위험)")
        
    if accessibility < 60:
        risks.append("농기계 및 수송 차량 접근 도로 협소 (접근성 취약)")
        
    if management_difficulty >= 45:
        risks.append("농지 내 잡초 무성 및 유휴 기간 장기화에 따른 초기 정비 작업 필요")
        
    if drone_details.get("facility_installation_score", 0) < 60:
        risks.append("경사도 또는 필지 불규칙성으로 인한 대규모 유리온실/스마트팜 설치 제한")

    if not risks:
        risks.append("특별한 단기 위험 요인은 없으나, 초기 영농 자금 확보 및 설비 구축 필요")

    # 3. 정책 추천 연계 로직
    policy_recommendations.append("청년 후계농 영농정착 지원금 연계 (월 최대 110만원)")
    
    if "스마트팜 딸기" in recommended_crops or "방울토마토" in recommended_crops:
        policy_recommendations.append("지자체 임대형 스마트팜 지원 사업 참여 권장")
        policy_recommendations.append("청년농업인 스마트팜 융복합 지원사업 (시설비 최대 70% 보조)")
    else:
        policy_recommendations.append("농지은행 청년농 선임대후매도사업 연계 지원")
        
    if accessibility >= 80:
        policy_recommendations.append("농촌 융복합 산업(6차 산업) 활성화 지원 및 체험 농장 국비 연계")

    if drainage_risk >= 30:
        policy_recommendations.append("농수산식품공사 배수개선 및 흙넣기(객토) 지원 사업 연계")

    # 4. 분석 요약 텍스트 생성
    region = candidate_info.get("region", "해당 지역")
    land_type = candidate_info.get("land_type", "농지")
    
    summary_parts = []
    summary_parts.append(f"{region}에 위치한 본 {land_type}(은/는) 토양 적성 점수가 {soil_score}점으로 ")
    
    if soil_score >= 80:
        summary_parts.append("기본 토양 환경이 매우 우수합니다. ")
    else:
        summary_parts.append("일반적인 토양 수준을 가지고 있습니다. ")
        
    if drainage_risk >= 30:
        summary_parts.append("다만 드론 열화상 분석 결과 일부 구역에 저온/과습 현상이 관측되어 배수 관리가 시급합니다. ")
    else:
        summary_parts.append("드론 열화상 분석 결과 수분 분포가 매우 고르고 안정적이어서 작물 생육에 유리합니다. ")
        
    if drone_details.get("facility_installation_score", 0) >= 75:
        summary_parts.append("필지 형태가 비교적 균일하고 평평하여 시설(스마트팜 등) 설치에 매우 적합합니다. ")
        crops_str = " 및 ".join(recommended_crops[:2])
        summary_parts.append(f"따라서 고부가가치를 창출할 수 있는 {crops_str} 재배를 적극 권장합니다.")
    else:
        summary_parts.append("경사지나 불규칙성이 존재하여 대형 시설물보다는 노지 재배 또는 체험 농장 형태가 유리합니다. ")
        crops_str = " 및 ".join(recommended_crops[:2])
        summary_parts.append(f"따라서 {crops_str} 등의 품목이 추천됩니다.")
        
    analysis_summary = "".join(summary_parts)

    return recommended_crops, risks, policy_recommendations, analysis_summary
