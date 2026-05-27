import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple

def analyze_rgb_image(image_path_or_obj) -> Tuple[Dict[str, Any], np.ndarray]:
    """RGB 드론 이미지 분석을 수행합니다.
    식생 밀도, 나지 비율, 농지 균일성(정리 상태), 시설 설치 가능성을 평가하고
    각 영역을 표시한 시각화 오버레이 이미지를 반환합니다.
    
    Args:
        image_path_or_obj: 이미지 파일 경로(str) 또는 PIL Image 객체
        
    Returns:
        Tuple[Dict[str, Any], np.ndarray]: (분석 결과 딕셔너리, 시각화 완료된 OpenCV BGR 이미지)
    """
    # 이미지 로드
    img = None
    if isinstance(image_path_or_obj, str):
        # 한글 경로 지원을 위해 np.fromfile 사용
        try:
            img_array = np.fromfile(image_path_or_obj, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            img = None
    elif isinstance(image_path_or_obj, Image.Image):
        # PIL Image를 OpenCV BGR로 변환
        img_rgb = np.array(image_path_or_obj)
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    elif isinstance(image_path_or_obj, np.ndarray):
        # OpenCV 이미지(numpy 배열)인 경우 그대로 복사 사용
        img = image_path_or_obj.copy()

    # 이미지가 제대로 로드되지 않은 경우 Dummy 이미지 생성
    if img is None:
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        # 더미로 초록색(식생), 갈색(토양) 사각형 그리기
        cv2.rectangle(img, (0, 0), (300, 400), (45, 139, 87), -1)  # 초록색 농지
        cv2.rectangle(img, (300, 0), (600, 400), (30, 105, 210), -1) # 갈색 흙
        cv2.putText(img, "DUMMY RGB IMAGE", (180, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    h, w, _ = img.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1. 식생 검출 (Green Area)
    # Hue: 35~85 (초록색 범위)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = cv2.countNonZero(green_mask)

    # 2. 황토/나지 검출 (Brown/Bare Soil Area)
    # Hue: 10~25 (주황/갈색 범위)
    lower_brown = np.array([10, 40, 40])
    upper_brown = np.array([25, 255, 255])
    brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
    brown_pixels = cv2.countNonZero(brown_mask)

    total_pixels = h * w
    vegetation_ratio = float(green_pixels / total_pixels) * 100
    brown_ratio = float(brown_pixels / total_pixels) * 100
    other_ratio = 100.0 - vegetation_ratio - brown_ratio

    # 3. 농지 균일성(Field Uniformity) 분석
    # 에지(Edge) 검출을 통해 농지의 불규칙함이나 잡초, 방치 흔적 분석
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(cv2.countNonZero(edges) / total_pixels) * 100
    # 에지 밀도가 너무 높으면 지저분하게 방치된 농지(예: 무성한 잡초)로 보아 감점
    field_uniformity_score = max(0, min(100, 100 - (edge_density * 8)))

    # 4. 시설 설치 가능성 (Flat & Cleared area)
    # 나지(토양) 비율이 적절히 확보되어 있거나 정리가 잘 되어 있는 경우 높은 점수 부여
    # 에지가 적고(평평함), 극단적인 장애물이 없는 경우
    facility_installation_score = max(0, min(100, 80 + (brown_ratio * 0.3) - (edge_density * 4)))

    # 시각화 오버레이 (Overlay)
    # 녹색 식생 구역은 초록색 테두리로, 갈색 흙 구역은 주황색 테두리로 하이라이트
    overlay = img.copy()
    
    # 식생 반투명 마스크
    overlay[green_mask > 0] = overlay[green_mask > 0] * 0.7 + np.array([0, 150, 0]) * 0.3
    # 나지 반투명 마스크
    overlay[brown_mask > 0] = overlay[brown_mask > 0] * 0.7 + np.array([0, 80, 180]) * 0.3
    
    # 결과 합성 (투명도 0.6)
    visualized_img = cv2.addWeighted(img, 0.4, overlay.astype(np.uint8), 0.6, 0)
    
    # 분석정보 텍스트 추가
    cv2.putText(visualized_img, f"Veg Ratio: {vegetation_ratio:.1f}%", (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(visualized_img, f"Soil Ratio: {brown_ratio:.1f}%", (15, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    cv2.putText(visualized_img, f"Uniformity: {field_uniformity_score:.1f}", (15, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    metrics = {
        "vegetation_ratio": round(vegetation_ratio, 1),
        "brown_or_bare_soil_ratio": round(brown_ratio, 1),
        "field_uniformity_score": round(field_uniformity_score, 1),
        "facility_installation_score": round(facility_installation_score, 1)
    }

    return metrics, visualized_img
