import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple

def analyze_thermal_image(image_path_or_obj) -> Tuple[Dict[str, Any], np.ndarray]:
    """열화상 드론 이미지 분석을 수행합니다.
    (주의: 본 MVP는 방사율(Radiometric) 메타데이터가 없는 일반 이미지 기준이므로,
    Grayscale Intensity 밝기값을 온도로 가정하여 상대 분석을 수행합니다.)
    
    분석 항목:
    - cold_region_ratio: 저온 구역 비율 (과습/배수불량 의심)
    - hot_region_ratio: 고온 구역 비율 (건조/열스트레스 의심)
    - moisture_balance_score: 수분 균형 점수 (최적 온도대 분포 비중)
    - drainage_risk_score: 배수 위험 점수 (저온 구역 비율 기반)
    - temperature_variation_score: 온도 편차 균일성 점수
    
    Args:
        image_path_or_obj: 이미지 파일 경로(str) 또는 PIL Image 객체
        
    Returns:
        Tuple[Dict[str, Any], np.ndarray]: (분석 결과 딕셔너리, 시각화 완료된 OpenCV BGR 이미지)
    """
    # 이미지 로드
    img = None
    if isinstance(image_path_or_obj, str):
        try:
            img_array = np.fromfile(image_path_or_obj, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            img = None
    elif isinstance(image_path_or_obj, Image.Image):
        img_rgb = np.array(image_path_or_obj)
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # 이미지가 제대로 로드되지 않은 경우 Dummy 이미지 생성
    if img is None:
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        # 더미 그라데이션 그리기 (온도 스펙트럼처럼 보이게)
        for i in range(600):
            val = int((i / 600) * 255)
            img[:, i] = [val, 0, 255 - val] # Blue to Red gradient
        # 일부 구역에 물 웅덩이(파란색)와 건조 지역(빨간색) 그리기
        cv2.circle(img, (150, 150), 60, (255, 0, 0), -1) # 파란 물웅덩이
        cv2.circle(img, (450, 250), 80, (0, 0, 255), -1) # 빨간 열 축적 구역
        cv2.putText(img, "DUMMY THERMAL IMAGE", (140, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    h, w, _ = img.shape
    
    # 1. Grayscale 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    total_pixels = h * w

    # 2. 임계값 기반 구역 구분
    # 밝기값이 낮을수록 저온(배수 불량/과습), 높을수록 고온(건조)으로 정의
    # (일반적으로 물은 열용량이 커서 낮에 온도가 낮게 잡히고, 마른 흙/돌은 열용량이 작아 온도가 높음)
    cold_threshold = 85
    hot_threshold = 170

    cold_mask = cv2.inRange(gray, 0, cold_threshold)
    hot_mask = cv2.inRange(gray, hot_threshold, 255)

    cold_pixels = cv2.countNonZero(cold_mask)
    hot_pixels = cv2.countNonZero(hot_mask)

    cold_ratio = float(cold_pixels / total_pixels) * 100
    hot_ratio = float(hot_pixels / total_pixels) * 100
    normal_ratio = 100.0 - cold_ratio - hot_ratio

    # 3. 온도 표준편차 분석 (Uniformity)
    std_dev = float(np.std(gray))
    # 표준편차가 클수록 온도 편차가 크고 불균일함 (가장 이상적인 농지는 10 내외, 30 이상이면 불균일)
    temperature_variation_score = max(0, min(100, 100 - (std_dev * 1.5)))

    # 4. 수분 균형 점수 (Moisture Balance)
    # 정상 범위(수분 적절) 비중이 높을수록 감점이 적어짐
    moisture_balance_score = max(0, min(100, normal_ratio + (cold_ratio * 0.4) + (hot_ratio * 0.2)))

    # 5. 배수 위험 점수 (Drainage Risk Score)
    # 저온 구역(수분 과다) 비중이 높을수록 위험 점수 증가
    drainage_risk_score = min(100, int(cold_ratio * 1.5))

    # 시각화 이미지 생성 (Thermal Colormap 적용)
    # 흙토람/드론 분석 느낌을 내기 위해 JET 컬러맵 적용
    thermal_color = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    # 위험구역 오버레이 표시 (저온/과습 구역은 파란색 경계선, 고온/건조 구역은 빨간색 경계선)
    # OpenCV contours를 찾아 외곽선을 그립니다.
    contours_cold, _ = cv2.findContours(cold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(thermal_color, contours_cold, -1, (255, 255, 0), 2) # 하늘색: 과습 의심 구역

    contours_hot, _ = cv2.findContours(hot_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(thermal_color, contours_hot, -1, (0, 0, 255), 2) # 빨간색: 건조 스트레스 의심 구역

    # 텍스트 오버레이 추가
    cv2.putText(thermal_color, f"Moisture Stress: {cold_ratio:.1f}%", (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(thermal_color, f"Heat Stress: {hot_ratio:.1f}%", (15, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(thermal_color, f"Drainage Risk: {drainage_risk_score}%", (15, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    metrics = {
        "cold_region_ratio": round(cold_ratio, 1),
        "hot_region_ratio": round(hot_ratio, 1),
        "temperature_variation_score": round(temperature_variation_score, 1),
        "moisture_balance_score": round(moisture_balance_score, 1),
        "drainage_risk_score": int(drainage_risk_score)
    }

    return metrics, thermal_color
