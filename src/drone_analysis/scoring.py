import os
import yaml
from typing import Dict, Any, Tuple

def load_scoring_weights() -> Dict[str, Any]:
    """scoring_weights.yaml 설정 파일을 로드합니다.
    파일이 없을 경우 코드 내 기본값을 반환합니다.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.abspath(os.path.join(current_dir, "..", "..", "configs", "scoring_weights.yaml"))
    
    default_weights = {
        "public_weights": {
            "soil_crop_score": 0.25,
            "agricultural_zone_score": 0.20,
            "actual_farmland_score": 0.15,
            "accessibility_score": 0.15,
            "drainage_slope_score": 0.10,
            "geo_environment_score": 0.10,
            "youth_policy_score": 0.05
        },
        "drone_weights": {
            "vegetation_health_score": 0.25,
            "moisture_balance_score": 0.20,
            "field_condition_score": 0.20,
            "drainage_risk_reverse_score": 0.15,
            "facility_installation_score": 0.10,
            "management_difficulty_reverse_score": 0.10
        },
        "final_weights": {
            "public_api_score": 0.50,
            "drone_analysis_score": 0.35,
            "youth_policy_score": 0.15
        }
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    return config
        except Exception as e:
            print(f"Error loading weights config: {e}. Using default weights.")
            
    return default_weights

def calculate_drone_score(rgb_metrics: Dict[str, Any], thermal_metrics: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """RGB 및 열화상 분석 메트릭을 바탕으로 2차 드론 분석 점수를 산출합니다.
    
    Args:
        rgb_metrics (Dict[str, Any]): RGB 이미지 분석 결과
        thermal_metrics (Dict[str, Any]): 열화상 이미지 분석 결과
        
    Returns:
        Tuple[float, Dict[str, Any]]: (최종 2차 드론 점수, 상세 점수 매핑 정보)
    """
    weights = load_scoring_weights()["drone_weights"]
    
    # 1. 식생 건강도 점수 (식생 비율이 너무 낮으면 방치 또는 비경작지로 간주하되 적정 범위 점수화)
    # 50% 수준일 때 가장 건강하다고 가정하거나, 수치가 높을 수록 식생 밀도가 높음
    # 여기서는 식생 비율(vegetation_ratio)을 식생 건강도 점수의 기본값으로 매핑
    vegetation_health_score = min(100.0, rgb_metrics.get("vegetation_ratio", 70.0) + 15.0)
    
    # 2. 수분 균형 점수 (열화상 moisture_balance_score 연동)
    moisture_balance_score = thermal_metrics.get("moisture_balance_score", 80.0)
    
    # 3. 농지 정리 상태 (RGB field_uniformity_score 연동)
    field_condition_score = rgb_metrics.get("field_uniformity_score", 75.0)
    
    # 4. 배수 위험 역산 점수 (낮은 위험 = 높은 점수)
    drainage_risk_score = thermal_metrics.get("drainage_risk_score", 20)
    drainage_risk_reverse_score = 100.0 - drainage_risk_score
    
    # 5. 시설 설치 가능성 (RGB facility_installation_score 연동)
    facility_installation_score = rgb_metrics.get("facility_installation_score", 80.0)
    
    # 6. 관리 난이도 역산 점수 (에지 밀도가 낮고 정리가 잘 될 수록 관리가 쉬움)
    # RGB의 field_uniformity가 높을수록 난이도가 낮다고 평가
    management_difficulty_score = max(0, min(100, int((100 - field_condition_score) * 1.2)))
    management_difficulty_reverse_score = 100.0 - management_difficulty_score

    # 가중치 계산
    score = (
        weights["vegetation_health_score"] * vegetation_health_score +
        weights["moisture_balance_score"] * moisture_balance_score +
        weights["field_condition_score"] * field_condition_score +
        weights["drainage_risk_reverse_score"] * drainage_risk_reverse_score +
        weights["facility_installation_score"] * facility_installation_score +
        weights["management_difficulty_reverse_score"] * management_difficulty_reverse_score
    )
    
    details = {
        "vegetation_health_score": round(vegetation_health_score, 1),
        "moisture_balance_score": round(moisture_balance_score, 1),
        "field_condition_score": round(field_condition_score, 1),
        "drainage_risk_score": drainage_risk_score,
        "drainage_risk_reverse_score": round(drainage_risk_reverse_score, 1),
        "facility_installation_score": round(facility_installation_score, 1),
        "management_difficulty_score": management_difficulty_score,
        "management_difficulty_reverse_score": round(management_difficulty_reverse_score, 1)
    }
    
    return round(score, 2), details

def calculate_final_score(public_score: float, drone_score: float, youth_policy_score: float) -> Tuple[float, str]:
    """1차 공공 점수, 2차 드론 점수, 3차 청년 정책 지원 점수를 바탕으로 최종 창농 적합도를 산출합니다.
    
    Args:
        public_score (float): 1차 공공데이터 평가 점수
        drone_score (float): 2차 드론 이미지 분석 점수
        youth_policy_score (float): 청년 정책 점수
        
    Returns:
        Tuple[float, str]: (최종 적합도 점수, 적합도 등급)
    """
    weights = load_scoring_weights()["final_weights"]
    
    final_score = (
        weights["public_api_score"] * public_score +
        weights["drone_analysis_score"] * drone_score +
        weights["youth_policy_score"] * youth_policy_score
    )
    
    final_score = round(final_score, 2)
    
    # 등급 산출
    # 85 이상: 매우 적합
    # 70 이상: 적합
    # 55 이상: 조건부 적합
    # 55 미만: 부적합 또는 개선 필요
    if final_score >= 85:
        grade = "매우 적합"
    elif final_score >= 70:
        grade = "적합"
    elif final_score >= 55:
        grade = "조건부 적합"
    else:
        grade = "부적합 또는 개선 필요"
        
    return final_score, grade
