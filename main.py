import os
import json
import base64
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# .env 파일 수동 로드
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                parts = line.split("=", 1)
                os.environ[parts[0].strip()] = parts[1].strip()

# 모듈 임포트
from src.public_data.mock_loader import load_mock_candidates
from src.utils.io import export_result_json

app = FastAPI(
    title="청년 농업 창업 입지 진단 API",
    description="공공 데이터 및 드론 영상 분석 기반 입지 진단 API 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

# 프로젝트 루트 경로 확보
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
REACT_BUILD_DIR = os.path.join(STATIC_DIR, "react-app")
REACT_INDEX_PATH = os.path.join(REACT_BUILD_DIR, "index.html")
REACT_DASHBOARD_PATH = os.path.join(REACT_BUILD_DIR, "dashboard.html")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SAMPLE_IMG_DIR = os.path.join(DATA_DIR, "sample_images")

# Helper: 한글 경로 지원 OpenCV 이미지 읽기/쓰기 함수
def cv2_imread_unicode(path, flags=None):
    try:
        import cv2
        import numpy as np
        img_array = np.fromfile(path, np.uint8)
        read_flags = flags if flags is not None else cv2.IMREAD_COLOR
        return cv2.imdecode(img_array, read_flags)
    except Exception:
        return None

def cv2_imwrite_unicode(path, img) -> bool:
    try:
        import cv2
        import numpy as np
        ext = os.path.splitext(path)[1]
        ret, buf = cv2.imencode(ext, img)
        if ret:
            with open(path, "wb") as f:
                f.write(buf.tobytes())
            return True
    except Exception as e:
        print(f"cv2_imwrite_unicode failed for {path}: {e}")
    return False

# 기본 이미지 자동 생성 함수 임포트 구동 (app.py에 있던 로직 이관)
def ensure_sample_images():
    try:
        import cv2
        import numpy as np
    except ImportError:
        return False

    os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)
    rgb_path = os.path.join(SAMPLE_IMG_DIR, "sample_rgb.png")
    thermal_path = os.path.join(SAMPLE_IMG_DIR, "sample_thermal.png")
    
    if not os.path.exists(rgb_path):
        rgb_img = np.zeros((400, 600, 3), dtype=np.uint8)
        rgb_img[:, :] = [45, 139, 87]  # Green background
        cv2.rectangle(rgb_img, (350, 50), (550, 350), (30, 105, 200), -1)  # Bare soil
        cv2.rectangle(rgb_img, (50, 80), (180, 220), (220, 220, 220), -1)  # Greenhouse outline
        cv2.putText(rgb_img, "Greenhouse Setup", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        cv2_imwrite_unicode(rgb_path, rgb_img)
        
    if not os.path.exists(thermal_path):
        thermal_img = np.zeros((400, 600, 3), dtype=np.uint8)
        for i in range(600):
            val = int(80 + (i / 600) * 100)
            thermal_img[:, i] = [val, val, val]
        cv2.circle(thermal_img, (200, 250), 70, (30, 30, 30), -1)  # Wet spot
        cv2.circle(thermal_img, (480, 150), 60, (230, 230, 230), -1)  # Dry/hot spot
        cv2_imwrite_unicode(thermal_path, thermal_img)

    return True

# Helper: OpenCV 이미지를 Base64 스트링으로 변환
def encode_image_to_base64(img_bgr) -> str:
    import cv2

    _, buffer = cv2.imencode('.png', img_bgr)
    return base64.b64encode(buffer).decode('utf-8')

# .env 파일 수동 로드 (추가 라이브러리 없이 구현)
def load_dotenv():
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    os.environ[key] = val

load_dotenv()

# 설정값 프론트 서빙 API
@app.get("/api/config")
def get_config():
    return {
        "vworld_api_key": os.getenv("VWORLD_API_KEY", "")
    }

# 루트 주소 접속 시 랜딩페이지 서빙
@app.get("/")
def read_root():
    if os.path.exists(REACT_INDEX_PATH):
        return FileResponse(REACT_INDEX_PATH)
    return {"message": "FastAPI Server is running. React build not found. Run 'npm run build' first."}

# SPA 직접 접속 또는 기존 대시보드 경로 호환
@app.get("/app")
def read_dashboard():
    if os.path.exists(REACT_DASHBOARD_PATH):
        return FileResponse(REACT_DASHBOARD_PATH)
    if os.path.exists(REACT_INDEX_PATH):
        return FileResponse(REACT_INDEX_PATH)
    return {"message": "FastAPI Server is running. React build not found. Run 'npm run build' first."}

@app.get("/dashboard")
def read_dashboard_page():
    if os.path.exists(REACT_DASHBOARD_PATH):
        return FileResponse(REACT_DASHBOARD_PATH)
    if os.path.exists(REACT_INDEX_PATH):
        return FileResponse(REACT_INDEX_PATH)
    return {"message": "FastAPI Server is running. React build not found. Run 'npm run build' first."}

# 1. 1차 후보 농지 목록 조회 API
@app.get("/api/candidates")
def get_candidates():
    try:
        candidates = load_mock_candidates()
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 드론 이미지 공간 분석 및 추천 실행 API
@app.post("/api/analyze")
async def analyze_drone_data(
    candidate_id: str = Form(...),
    rgb_file: Optional[UploadFile] = File(None),
    thermal_file: Optional[UploadFile] = File(None),
    use_sample: bool = Form(True),
    crop_name: Optional[str] = Form(None),
    monthly_net_profit: Optional[float] = Form(None),
    required_area: Optional[float] = Form(None)
):
    try:
        import cv2
        import numpy as np
        from src.drone_analysis.rgb_analysis import analyze_rgb_image
        from src.drone_analysis.thermal_analysis import analyze_thermal_image
        from src.drone_analysis.scoring import calculate_drone_score, calculate_final_score
        from src.recommendation.crop_recommender import recommend_crops
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Drone analysis dependencies are not installed: {exc}"
        )

    ensure_sample_images()

    # 1. 후보지 정보 로드
    candidates = load_mock_candidates()
    candidate = next((c for c in candidates if c["candidate_id"] == candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate land not found")

    # 2. 이미지 읽기 및 디코딩
    # RGB 처리
    rgb_img = None
    if rgb_file and rgb_file.filename != "":
        contents = await rgb_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        rgb_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif use_sample:
        sample_path = os.path.join(SAMPLE_IMG_DIR, "sample_rgb.png")
        rgb_img = cv2_imread_unicode(sample_path)
        
    # Thermal 처리
    thermal_img = None
    if thermal_file and thermal_file.filename != "":
        contents = await thermal_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        thermal_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif use_sample:
        sample_path = os.path.join(SAMPLE_IMG_DIR, "sample_thermal.png")
        thermal_img = cv2_imread_unicode(sample_path)

    if rgb_img is None or thermal_img is None:
        raise HTTPException(
            status_code=400, 
            detail="Images could not be loaded. Please upload valid files or select sample mode."
        )

    try:
        # 3. 드론 이미지 공간 정보 분석
        # rgb_analysis
        rgb_metrics, rgb_visualized = analyze_rgb_image(rgb_img)
        # thermal_analysis
        thermal_metrics, thermal_visualized = analyze_thermal_image(thermal_img)
        # 4. 분석 점수 계산
        drone_score, drone_details = calculate_drone_score(rgb_metrics, thermal_metrics)
        # 5. 최종 종합 점수 산출
        public_score = candidate["public_api_score"]
        youth_policy_score = candidate["youth_policy_score"]
        final_score, suitability_grade = calculate_final_score(public_score, drone_score, youth_policy_score)
        
        # 6. 추천 항목 생성
        recommended_crops, risks, policy_recommendations, analysis_summary = recommend_crops(
            candidate, drone_details
        )
        
        # 6.1 Gemini AI 리포트 생성 시도
        gemini_report = None
        if os.getenv("GEMINI_API_KEY"):
            try:
                from src.recommendation.gemini_recommender import get_gemini_recommendation
                income_plan = {
                    "crop": {"name": crop_name or "미지정"},
                    "monthlyNetProfit": int(monthly_net_profit) if monthly_net_profit else 0,
                    "requiredArea": int(required_area) if required_area else 0
                }
                gemini_res = get_gemini_recommendation(candidate, drone_details, income_plan)
                gemini_report = {
                    "analysis_summary": gemini_res.analysis_summary,
                    "risks_solutions": [
                        {
                            "element": r.element,
                            "cause": r.cause,
                            "solution": r.solution
                        } for r in gemini_res.risks_solutions
                    ],
                    "policy_tips": gemini_res.policy_tips,
                    "startup_roadmap": gemini_res.startup_roadmap
                }
                # Gemini 결과가 성공하면 기본 결과의 일부 항목 대체/강화
                analysis_summary = gemini_res.analysis_summary
                risks = [f"{r.element}: {r.solution} ({r.cause})" for r in gemini_res.risks_solutions]
                policy_recommendations = gemini_res.policy_tips
            except Exception as e:
                print(f"Gemini recommendation failed, falling back: {e}")
        
        # 7. 이미지 Base64 인코딩
        rgb_vis_b64 = encode_image_to_base64(rgb_visualized)
        thermal_vis_b64 = encode_image_to_base64(thermal_visualized)
        
        # 원본 이미지도 Base64 반환 (프론트엔드 시연 편의성용)
        rgb_orig_b64 = encode_image_to_base64(rgb_img)
        thermal_orig_b64 = encode_image_to_base64(thermal_img)

        # 8. 최종 결과 구조화
        result = {
            "candidate_id": candidate_id,
            "region": candidate["region"],
            "address": candidate["address"],
            "location": {
                "lat": candidate["lat"],
                "lng": candidate["lng"]
            },
            "area_m2": candidate["area_m2"],
            "land_type": candidate["land_type"],
            "public_api_score": public_score,
            "drone_analysis_score": drone_score,
            "final_startup_suitability": final_score,
            "suitability_grade": suitability_grade,
            "recommended_crops": recommended_crops,
            "risks": risks,
            "policy_recommendations": policy_recommendations,
            "analysis_summary": analysis_summary,
            "gemini_report": gemini_report,
            "images": {
                "rgb_original": f"data:image/png;base64,{rgb_orig_b64}",
                "rgb_visualized": f"data:image/png;base64,{rgb_vis_b64}",
                "thermal_original": f"data:image/png;base64,{thermal_orig_b64}",
                "thermal_visualized": f"data:image/png;base64,{thermal_vis_b64}"
            },
            "analysis": {
                "public_data": {
                    "soil_crop_score": candidate["soil_crop_score"],
                    "agricultural_zone_score": candidate["agricultural_zone_score"],
                    "actual_farmland_score": candidate["actual_farmland_score"],
                    "accessibility_score": candidate["accessibility_score"],
                    "drainage_slope_score": candidate["drainage_slope_score"],
                    "geo_environment_score": candidate["geo_environment_score"],
                    "youth_policy_score": candidate["youth_policy_score"]
                },
                "drone_data": drone_details
            }
        }
        
        # 내부 디스크 백업 저장 (outputs/results/ 디렉토리)
        export_result_json(result, candidate_id)

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# 3. 결과 JSON 리포트 디스크 백업 수동 API
class ExportRequest(BaseModel):
    result_data: Dict[str, Any]
    candidate_id: str

@app.post("/api/export")
def export_results(payload: ExportRequest):
    try:
        file_path = export_result_json(payload.result_data, payload.candidate_id)
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 정적 파일 서빙용 StaticFiles 마운트 (/static 하위)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
