import os
import json
from typing import List, Dict, Any

def get_data_dir() -> str:
    """데이터 디렉토리 경로를 반환합니다."""
    # src/public_data/mock_loader.py 기준으로 프로젝트 루트 폴더 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    return os.path.join(project_root, "data")

def load_mock_candidates() -> List[Dict[str, Any]]:
    """mock_candidates.json 파일을 읽어서 후보지 목록을 반환합니다.
    
    Returns:
        List[Dict[str, Any]]: 후보 농지 데이터 목록
    """
    data_dir = get_data_dir()
    file_path = os.path.join(data_dir, "mock_candidates.json")
    
    if not os.path.exists(file_path):
        # 만약 파일이 없다면 기본 데이터 리스트를 반환합니다. (에러 방지)
        return [
            {
                "candidate_id": "FARM-001",
                "region": "경상북도 상주시",
                "address": "경상북도 상주시 사벌국면 삼덕리 120-5",
                "lat": 36.4528,
                "lng": 128.2195,
                "area_m2": 3200,
                "land_type": "답 (논)",
                "soil_crop_score": 85,
                "agricultural_zone_score": 90,
                "actual_farmland_score": 95,
                "accessibility_score": 88,
                "drainage_slope_score": 80,
                "geo_environment_score": 82,
                "youth_policy_score": 90,
                "public_api_score": 87.4
            }
        ]
        
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
