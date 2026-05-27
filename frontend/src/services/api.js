import fallbackCandidates from '../../../data/mock_candidates.json';

export async function getCandidates() {
  try {
    const response = await fetch('/api/candidates');
    if (!response.ok) throw new Error(`후보지 조회 실패 (${response.status})`);
    return await response.json();
  } catch (error) {
    return fallbackCandidates;
  }
}

export async function analyzeDroneImages({ candidateId, rgbFile, thermalFile, useSample, cropName, monthlyNetProfit, requiredArea }) {
  const formData = new FormData();
  formData.append('candidate_id', candidateId);
  formData.append('use_sample', String(useSample));
  if (cropName) formData.append('crop_name', cropName);
  if (monthlyNetProfit) formData.append('monthly_net_profit', String(monthlyNetProfit));
  if (requiredArea) formData.append('required_area', String(requiredArea));
  
  if (rgbFile) formData.append('rgb_file', rgbFile);
  if (thermalFile) formData.append('thermal_file', thermalFile);

  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `드론 분석 실패 (${response.status})`);
  }
  return payload;
}
