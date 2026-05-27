import os
import json
from typing import Dict, Any

def get_project_root() -> str:
    """프로젝트 루트 폴더 경로를 반환합니다."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))

def ensure_output_dir() -> str:
    """출력 결과를 보관할 outputs/results/ 디렉토리를 생성하고 경로를 반환합니다."""
    root = get_project_root()
    output_dir = os.path.join(root, "outputs", "results")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def export_result_json(result_data: Dict[str, Any], candidate_id: str) -> str:
    """진단 결과를 JSON 파일로 저장하고 저장된 파일 경로를 반환합니다.
    
    Args:
        result_data (Dict[str, Any]): 저장할 결과 데이터
        candidate_id (str): 후보 농지 ID
        
    Returns:
        str: 저장된 JSON 파일 경로
    """
    output_dir = ensure_output_dir()
    file_name = f"result_{candidate_id}.json"
    file_path = os.path.join(output_dir, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
        
    return file_path
