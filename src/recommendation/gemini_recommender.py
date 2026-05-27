import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class RiskSolution(BaseModel):
    element: str = Field(description="위험 요소명")
    cause: str = Field(description="원인 또는 상태 분석")
    solution: str = Field(description="구체적 해결 방안 또는 대처 솔루션")

class GeminiRecommendationResponse(BaseModel):
    analysis_summary: str = Field(description="후보 농지의 장단점과 종합 입지 분석 총평")
    risks_solutions: List[RiskSolution] = Field(description="탐지된 위험 요인 및 이를 극복하기 위한 구체적인 솔루션 목록")
    policy_tips: List[str] = Field(description="해당 지자체에서 활용할 수 있는 추천 정책 사업 및 실질적 조언")
    startup_roadmap: List[str] = Field(description="이 땅에서 창농을 시작하기 위한 4단계 실행 로드맵")

def get_gemini_recommendation(candidate_info: Dict[str, Any], drone_details: Dict[str, Any], income_plan: Dict[str, Any]) -> GeminiRecommendationResponse:
    """Gemini 2.5 Flash API를 호출하여 구조화된 귀농 추천 결과를 가져옵니다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    당신은 대한민국 농림축산식품부 산하의 최정예 귀농·창농 전문 컨설턴트입니다.
    제공된 데이터(목표 소득, 공공 평가 점수, 드론 영상 분석 지표)를 종합적으로 정밀 분석하여,
    이 후보 농지에 정착하려는 청년 창업농에게 현실적이고 구체적인 전문 리포트를 작성해 주세요.
    
    [분석 대상 데이터]
    1. 청년농의 창농 목표:
       - 희망 재배 방식/작물: {income_plan.get('crop', {}).get('name', '미지정')}
       - 목표 월 순이익: {income_plan.get('monthlyNetProfit', '계산 필요')}원
       - 목표 재배 면적: {income_plan.get('requiredArea', '계산 필요')}평
       
    2. 후보지 공공 정보:
       - 주소: {candidate_info.get('address')}
       - 지적 유형: {candidate_info.get('land_type')}
       - 토양 적성: {candidate_info.get('soil_crop_score')}점
       - 접근성 점수: {candidate_info.get('accessibility_score')}점
       - 청년농 정책 점수: {candidate_info.get('youth_policy_score')}점
       - 공공 종합 API 점수: {candidate_info.get('public_api_score')}점
       
    3. 드론 원격 탐사 데이터:
       - 식생 상태 점수: {drone_details.get('vegetation_health_score')}점
       - 수분 분포 균형: {drone_details.get('moisture_balance_score')}점
       - 필지 정돈 상태: {drone_details.get('field_condition_score')}점
       - 배수 위험도 점수: {drone_details.get('drainage_risk_score')}점 (높을수록 불량)
       - 시설(스마트팜 등) 구축 가능성: {drone_details.get('facility_installation_score')}점
       
    반드시 제공된 한국 농업 현황 및 지자체별 실정에 맞춰 매우 구체적이고 현실적이며 실질적인 조언이 담긴 응답 양식을 채워 주세요.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiRecommendationResponse,
            temperature=0.3,
        ),
    )
    
    return GeminiRecommendationResponse.model_validate_json(response.text)
