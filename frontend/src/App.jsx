import { useEffect, useMemo, useState, useRef } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  CircleDollarSign,
  Download,
  Image as ImageIcon,
  LandPlot,
  MapPin,
  Play,
  Sparkles,
  TrendingUp,
  Upload
} from 'lucide-react';
import { defaultInputs, regions } from './data/agricultureData';
import { Sidebar } from './components/Sidebar';
import { SectionHeader } from './components/SectionHeader';
import { ScoreBar } from './components/ScoreBar';
import { Metric } from './components/Metric';
import { buildInvestmentOptions } from './utils/calculations';
import { formatNumber, formatPyeong, formatWon } from './utils/formatters';
import { analyzeDroneImages, getCandidates } from './services/api';

const landingHref = import.meta.env.DEV ? import.meta.env.BASE_URL : '/';

const preferenceDefaults = {
  infra: 3,
  education: 3,
  sea: 3,
  nature: 3,
  metropolis: 3,
  landPrice: 3,
  subsidy: 3,
  community: 3
};

const preferenceLabels = [
  ['infra', '생활 인프라', '병원, 마트, 교통 등 정주 여건'],
  ['education', '교육 접근성', '자녀 교육과 학습 시설'],
  ['sea', '해안 접근성', '바다 인접 생활 선호'],
  ['nature', '자연 환경', '조용하고 넓은 농촌 환경'],
  ['metropolis', '대도시 접근성', '도시권 이동 편의성'],
  ['landPrice', '낮은 농지 비용', '초기 투자비 절감'],
  ['subsidy', '지원사업', '청년농 지원금과 지자체 정책'],
  ['community', '지역 커뮤니티', '귀농인 네트워크와 정착 지원']
];

const publicScoreLabels = {
  soil_crop_score: '토양/작물 적성',
  agricultural_zone_score: '농업진흥지역',
  actual_farmland_score: '실제 농경지',
  accessibility_score: '접근성',
  drainage_slope_score: '배수/경사',
  geo_environment_score: '지하수/지질',
  youth_policy_score: '청년정책'
};

export default function App() {
  const [activeSection, setActiveSection] = useState('income');
  const [inputs, setInputs] = useState(defaultInputs);
  const [preferences, setPreferences] = useState(preferenceDefaults);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [candidateStatus, setCandidateStatus] = useState('loading');
  const [droneForm, setDroneForm] = useState({ rgbFile: null, thermalFile: null, useSample: true });
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const selectedRegion = regions.find((region) => region.id === inputs.regionId);
  const options = useMemo(() => buildInvestmentOptions(inputs), [inputs]);
  const primaryPlan = options[0];
  const targetMonthlyIncome = Number(inputs.afterTaxSalary) / 12;
  const selectedCandidate = candidates.find((candidate) => candidate.candidate_id === selectedCandidateId) ?? candidates[0];
  const recommendedCandidate = useMemo(
    () => rankCandidates(candidates, preferences)[0],
    [candidates, preferences]
  );

  useEffect(() => {
    let isMounted = true;
    getCandidates()
      .then((items) => {
        if (!isMounted) return;
        setCandidates(items);
        setSelectedCandidateId(items[0]?.candidate_id ?? '');
        setCandidateStatus('ready');
      })
      .catch(() => {
        if (!isMounted) return;
        setCandidateStatus('error');
      });
    return () => {
      isMounted = false;
    };
  }, []);

  function updateInput(name, value) {
    setInputs((current) => ({
      ...current,
      [name]: name === 'afterTaxSalary' ? Number(value) : value
    }));
  }

  function updatePreference(name, value) {
    setPreferences((current) => ({
      ...current,
      [name]: Number(value)
    }));
  }

  async function handleDroneSubmit(event) {
    event.preventDefault();
    if (!selectedCandidate) return;
    setIsAnalyzing(true);
    setAnalysisError('');

    try {
      const result = await analyzeDroneImages({
        candidateId: selectedCandidate.candidate_id,
        rgbFile: droneForm.rgbFile,
        thermalFile: droneForm.thermalFile,
        useSample: droneForm.useSample,
        cropName: primaryPlan?.crop?.name ?? '',
        monthlyNetProfit: primaryPlan?.monthlyNetProfit ?? 0,
        requiredArea: primaryPlan?.requiredArea ?? 0
      });
      setAnalysisResult(result);
      setActiveSection('final');
    } catch (error) {
      setAnalysisError(error.message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  function downloadFinalJson() {
    const report = {
      income: primaryPlan,
      preferences,
      candidate: selectedCandidate,
      droneAnalysis: analysisResult,
      generatedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `farm_recommendation_${selectedCandidate?.candidate_id ?? 'result'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="dashboardShell">
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

      <main className="dashboardMain">
        <TopBar />

        {activeSection === 'income' && (
          <IncomeSection
            inputs={inputs}
            selectedRegion={selectedRegion}
            options={options}
            primaryPlan={primaryPlan}
            targetMonthlyIncome={targetMonthlyIncome}
            onInputChange={updateInput}
          />
        )}

        {activeSection === 'preferences' && (
          <PreferenceSection
            preferences={preferences}
            recommendedCandidate={recommendedCandidate}
            onPreferenceChange={updatePreference}
            onNext={() => setActiveSection('candidates')}
          />
        )}

        {activeSection === 'candidates' && (
          <CandidateSection
            status={candidateStatus}
            candidates={rankCandidates(candidates, preferences)}
            selectedCandidateId={selectedCandidateId}
            onSelect={setSelectedCandidateId}
            onNext={() => setActiveSection('drone')}
          />
        )}

        {activeSection === 'drone' && (
          <DroneSection
            selectedCandidate={selectedCandidate}
            droneForm={droneForm}
            analysisResult={analysisResult}
            analysisError={analysisError}
            isAnalyzing={isAnalyzing}
            onFormChange={setDroneForm}
            onSubmit={handleDroneSubmit}
          />
        )}

        {activeSection === 'final' && (
          <FinalSection
            primaryPlan={primaryPlan}
            selectedCandidate={selectedCandidate}
            recommendedCandidate={recommendedCandidate}
            preferences={preferences}
            analysisResult={analysisResult}
            onDownload={downloadFinalJson}
          />
        )}
      </main>
    </div>
  );
}

function TopBar() {
  return (
    <header className="dashboardTopbar">
      <div>
        <p className="eyebrow">COSS Hackerton MVP</p>
        <h1>귀농 소득·입지 통합 진단</h1>
      </div>
      <a href={landingHref} className="ghostButton">
        <ArrowLeft size={16} />
        랜딩으로
      </a>
    </header>
  );
}

function IncomeSection({ inputs, selectedRegion, options, primaryPlan, targetMonthlyIncome, onInputChange }) {
  const isInvalidSalary = !Number.isFinite(targetMonthlyIncome) || targetMonthlyIncome <= 0;

  return (
    <section className="dashboardSection">
      <SectionHeader
        eyebrow="Step 01"
        title="현재 세후소득을 농업 소득으로 대체하기"
        description="세후 연봉과 지역을 입력하면 같은 월 순이익을 만들기 위한 최소 초기비용 조합을 계산합니다."
      />

      <div className="twoColumn">
        <div className="glassCard">
          <div className="cardTitle">현재 조건</div>
          <NumberField
            label="세후 연봉"
            value={inputs.afterTaxSalary}
            step="1000000"
            onChange={(value) => onInputChange('afterTaxSalary', value)}
          />
          <label className="field">
            <span>지역 선택</span>
            <select value={inputs.regionId} onChange={(event) => onInputChange('regionId', event.target.value)}>
              <option value="">지역 선택 안 함 · 전국 최저비용</option>
              {regions.map((region) => (
                <option value={region.id} key={region.id}>
                  {region.name}
                </option>
              ))}
            </select>
          </label>
          <div className="dataGuide">
            <strong>계산 데이터</strong>
            <span>지역, 작물, 판매가격, 비용, 설정값을 JSON으로 분리해 관리합니다.</span>
          </div>
        </div>

        <div className="glassCard">
          <div className="cardTitle">계산 요약</div>
          {isInvalidSalary || !primaryPlan ? (
            <div className="emptyState">세후 연봉을 0보다 큰 값으로 입력해 주세요.</div>
          ) : (
            <>
              <div className="summaryTiles">
                <Metric icon={<CircleDollarSign />} label="목표 월 순이익" value={formatWon(targetMonthlyIncome)} />
                <Metric icon={<TrendingUp />} label="예상 월 매출" value={formatWon(primaryPlan.monthlyRevenue)} />
                <Metric icon={<LandPlot />} label="필요 규모" value={formatPyeong(primaryPlan.requiredArea)} />
              </div>
              <div className="highlightResult">
                <span>최소비용 조합</span>
                <strong>{primaryPlan.region.name} · {primaryPlan.crop.name}</strong>
                <em>{formatWon(primaryPlan.minimumInitialCost)}</em>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="optionGrid">
        {options.slice(0, 4).map((option) => (
          <InvestmentCard key={`${option.region.id}-${option.crop.id}`} option={option} />
        ))}
      </div>
    </section>
  );
}

function PreferenceSection({ preferences, recommendedCandidate, onPreferenceChange, onNext }) {
  return (
    <section className="dashboardSection">
      <SectionHeader
        eyebrow="Step 02"
        title="개인 맞춤형 입지 선호도 설정"
        description="입지 요인별 중요도를 설정하여 나에게 꼭 맞는 농지를 추천받으세요."
      />

      <div className="twoColumn">
        <div className="glassCard">
          <div className="cardTitle">8대 입지 요인</div>
          <div className="preferenceGrid">
            {preferenceLabels.map(([key, label, help]) => (
              <label key={key} className="rangeField">
                <div>
                  <strong>{label}</strong>
                  <span>{help}</span>
                </div>
                <output>{preferences[key]}점</output>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={preferences[key]}
                  onChange={(event) => onPreferenceChange(key, event.target.value)}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="glassCard recommendationPanel">
          <div className="cardTitle">선호도 반영 추천</div>
          {recommendedCandidate ? (
            <>
              <strong>{recommendedCandidate.address}</strong>
              <p>{recommendedCandidate.region} · {recommendedCandidate.land_type}</p>
              <ScoreBar label="선호도 보정 점수" value={recommendedCandidate.adjustedScore} />
              <ScoreBar label="공공 데이터 점수" value={recommendedCandidate.public_api_score} />
              <button type="button" className="primaryButton" onClick={onNext}>
                후보지 보기
              </button>
            </>
          ) : (
            <div className="emptyState">후보지 데이터를 불러오는 중입니다.</div>
          )}
        </div>
      </div>
    </section>
  );
}

function CandidateSection({ status, candidates, selectedCandidateId, onSelect, onNext }) {
  const selected = candidates.find((candidate) => candidate.candidate_id === selectedCandidateId) ?? candidates[0];
  const mapRef = useRef(null);
  const markersRef = useRef({});

  useEffect(() => {
    let isMounted = true;
    let mapInstance = null;

    async function initMap() {
      if (!document.getElementById('map-container')) return;

      let apiKey = "";
      try {
        const response = await fetch('/api/config');
        if (response.ok) {
          const data = await response.json();
          apiKey = data.vworld_api_key || "";
        }
      } catch (e) {
        console.error("Failed to load V-World config:", e);
      }

      if (!isMounted) return;

      const L = window.L;
      if (!L) {
        console.warn("Leaflet is not available on window.");
        return;
      }

      // Calculate center
      const lats = candidates.map(c => c.lat).filter(Boolean);
      const lngs = candidates.map(c => c.lng).filter(Boolean);
      const centerLat = lats.length ? (lats.reduce((a, b) => a + b, 0) / lats.length) : 36.5;
      const centerLng = lngs.length ? (lngs.reduce((a, b) => a + b, 0) / lngs.length) : 127.5;

      // Initialize map
      mapInstance = L.map('map-container').setView([centerLat, centerLng], 7);
      mapRef.current = mapInstance;

      // Default light base map
      const cartoLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
      });

      let baseMaps = {
        "기본 다크/라이트 맵": cartoLight
      };
      let overlayMaps = {};

      if (apiKey && apiKey.trim() !== "") {
        const vworldBase = L.tileLayer(`https://api.vworld.kr/req/wmts/1.0.0/${apiKey}/Base/{z}/{y}/{x}.png`, {
          maxZoom: 19,
          attribution: '© V-World Base'
        });

        const vworldSatellite = L.tileLayer(`https://api.vworld.kr/req/wmts/1.0.0/${apiKey}/Satellite/{z}/{y}/{x}.jpeg`, {
          maxZoom: 19,
          attribution: '© V-World Satellite'
        });

        const cadastralLayer = L.tileLayer.wms('https://api.vworld.kr/req/wms', {
          layers: 'lp_pa_cbnd_bonbun,lp_pa_cbnd_bubun',
          styles: 'lp_pa_cbnd_bonbun,lp_pa_cbnd_bubun,lp_pa_cbnd_bonbun_line,lp_pa_cbnd_bubun_line',
          format: 'image/png',
          transparent: true,
          version: '1.3.0',
          key: apiKey,
          domain: window.location.origin,
          attribution: '© V-World 지적도'
        });

        const agriZoneLayer = L.tileLayer.wms('https://api.vworld.kr/req/wms', {
          layers: 'LT_C_UQ111',
          styles: 'LT_C_UQ111',
          format: 'image/png',
          transparent: true,
          version: '1.3.0',
          key: apiKey,
          domain: window.location.origin,
          attribution: '© V-World 농업진흥지역'
        });

        vworldBase.addTo(mapInstance);

        baseMaps["브이월드 도로지도"] = vworldBase;
        baseMaps["브이월드 위성지도"] = vworldSatellite;
        overlayMaps["연속지적도 경계"] = cadastralLayer;
        overlayMaps["농업진흥지역 구역"] = agriZoneLayer;

        L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(mapInstance);
      } else {
        cartoLight.addTo(mapInstance);
      }

      // Add Markers
      const markerGroup = L.featureGroup().addTo(mapInstance);
      markersRef.current = {};

      candidates.forEach(c => {
        if (!c.lat || !c.lng) return;
        const score = c.adjustedScore !== undefined ? c.adjustedScore : c.public_api_score;
        const color = score >= 80 ? '#10b981' : (score >= 65 ? '#f59e0b' : '#ef4444');

        const marker = L.circleMarker([c.lat, c.lng], {
          radius: 12,
          fillColor: color,
          color: '#0b0f19',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(markerGroup);

        marker.bindPopup(`
          <div style="color: #0b0f19; font-family: 'Noto Sans KR'; font-size: 0.85rem; padding: 4px; line-height: 1.4;">
            <strong style="font-size: 0.9rem;">${c.candidate_id}</strong><br>
            <span style="font-size:0.75rem; color:#666;">${c.address}</span><br>
            <strong>공공 스코어: ${c.public_api_score}점</strong><br>
            <strong>맞춤 스코어: ${Number(score).toFixed(1)}점</strong>
          </div>
        `);

        marker.on('click', () => {
          onSelect(c.candidate_id);
        });

        markersRef.current[c.candidate_id] = marker;
      });

      if (candidates.length > 0) {
        mapInstance.fitBounds(markerGroup.getBounds().pad(0.2));
      }
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstance) {
        mapInstance.remove();
        mapRef.current = null;
      }
    };
  }, [candidates, onSelect]);

  // Selected candidate effect (center and zoom in)
  useEffect(() => {
    if (mapRef.current && selectedCandidateId) {
      const target = candidates.find(c => c.candidate_id === selectedCandidateId);
      if (target && target.lat && target.lng) {
        mapRef.current.setView([target.lat, target.lng], 16);
        const marker = markersRef.current[selectedCandidateId];
        if (marker) {
          marker.openPopup();
        }
      }
    }
  }, [selectedCandidateId, candidates]);

  return (
    <section className="dashboardSection">
      <SectionHeader
        eyebrow="Step 03"
        title="1차 농지 후보지 탐색 및 지형 분석"
        description="공공 데이터 및 브이월드 연속지적도/농업진흥지역 레이어를 지도로 탐색할 수 있습니다."
      />

      {status === 'error' && (
        <div className="noticeCard warning">
          <AlertTriangle size={18} />
          후보지 API 응답이 없어 로컬 목데이터를 사용합니다.
        </div>
      )}

      <div className="candidateLayout">
        <div className="candidateList">
          {candidates.map((candidate) => (
            <button
              type="button"
              key={candidate.candidate_id}
              className={candidate.candidate_id === selected?.candidate_id ? 'candidateCard active' : 'candidateCard'}
              onClick={() => onSelect(candidate.candidate_id)}
            >
              <span>{candidate.candidate_id}</span>
              <strong>{candidate.region}</strong>
              <em>{candidate.address}</em>
              <small>{candidate.land_type} · {candidate.area_m2.toLocaleString('ko-KR')}㎡</small>
            </button>
          ))}
        </div>

        <div className="glassCard">
          <div className="cardTitle">후보지 상세 평가</div>
          {selected ? (
            <>
              <div className="candidateHero">
                <div>
                  <span>{selected.candidate_id}</span>
                  <strong>{selected.address}</strong>
                </div>
                <b>{Number(selected.adjustedScore ?? selected.public_api_score).toFixed(1)}점</b>
              </div>
              <div className="scoreList">
                {Object.entries(publicScoreLabels).map(([key, label]) => (
                  <ScoreBar key={key} label={label} value={selected[key]} />
                ))}
              </div>
              <button type="button" className="primaryButton" onClick={onNext}>
                이 후보지로 드론 분석
              </button>
            </>
          ) : (
            <div className="emptyState">후보지를 불러오는 중입니다.</div>
          )}
        </div>
      </div>

      <div className="glassCard" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="cardTitle" style={{ margin: 0 }}>지적 공간 분포 지도</div>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            💡 지적도 경계 및 농업진흥지역 구역을 켜고 지도를 확대(+)하면 필지 경계선이 선명하게 나타납니다.
          </span>
        </div>
        <div
          id="map-container"
          style={{
            height: '420px',
            width: '100%',
            borderRadius: '12px',
            border: '1px solid var(--line)',
            background: 'var(--bg)',
            zIndex: 1
          }}
        ></div>
      </div>
    </section>
  );
}

function DroneSection({ selectedCandidate, droneForm, analysisResult, analysisError, isAnalyzing, onFormChange, onSubmit }) {
  return (
    <section className="dashboardSection">
      <SectionHeader
        eyebrow="Step 04"
        title="2차 미시 드론 영상 분석"
        description="드론으로 촬영된 RGB 및 열화상 이미지를 업로드하여 정밀 분석을 수행합니다."
      />

      <div className="twoColumn">
        <form className="glassCard uploadPanel" onSubmit={onSubmit}>
          <div className="cardTitle">원격 탐사 데이터 업로드</div>
          <div className="selectedLand">
            <MapPin size={18} />
            <span>{selectedCandidate ? selectedCandidate.address : '후보지를 먼저 선택하세요'}</span>
          </div>

          <FileField
            label="드론 RGB 이미지"
            file={droneForm.rgbFile}
            onChange={(file) => onFormChange((current) => ({ ...current, rgbFile: file }))}
          />
          <FileField
            label="드론 열화상 이미지"
            file={droneForm.thermalFile}
            onChange={(file) => onFormChange((current) => ({ ...current, thermalFile: file }))}
          />

          <label className="checkField">
            <input
              type="checkbox"
              checked={droneForm.useSample}
              onChange={(event) => onFormChange((current) => ({ ...current, useSample: event.target.checked }))}
            />
            업로드 파일이 없을 때 샘플 이미지 사용
          </label>

          <button type="submit" className="primaryButton" disabled={isAnalyzing || !selectedCandidate}>
            <Play size={17} />
            {isAnalyzing ? '분석 중...' : '드론 분석 실행'}
          </button>
        </form>

        <div className="glassCard">
          <div className="cardTitle">분석 결과</div>
          {analysisError && (
            <div className="noticeCard warning">
              <AlertTriangle size={18} />
              {analysisError}
            </div>
          )}
          {analysisResult ? (
            <DroneResult result={analysisResult} />
          ) : (
            <div className="emptyState">
              이미지 분석을 실행하면 식생, 수분, 배수, 시설 설치 가능성 지표가 표시됩니다.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function FinalSection({ primaryPlan, selectedCandidate, recommendedCandidate, preferences, analysisResult, onDownload }) {
  const candidate = selectedCandidate ?? recommendedCandidate;
  const finalScore = calculateFinalScore(candidate, analysisResult);

  return (
    <section className="dashboardSection">
      <SectionHeader
        eyebrow="Step 05"
        title="최종 창농 적합도 및 추천 결과"
        description="소득 대체 계산과 원본 입지 진단 흐름을 한 화면에서 종합합니다."
      />

      <div className="resultBanner">
        <div>
          <span>최종 추천</span>
          <h2>{primaryPlan ? `${primaryPlan.region.name} · ${primaryPlan.crop.name}` : '계산 결과 없음'}</h2>
          <p>
            {candidate
              ? `${candidate.address} 후보지를 기준으로 검토합니다.`
              : '후보지 데이터를 불러온 뒤 최종 추천이 표시됩니다.'}
          </p>
        </div>
        <strong>{finalScore.toFixed(1)}점</strong>
      </div>

      <div className="summaryTiles finalTiles">
        <Metric icon={<CircleDollarSign />} label="필요 초기비용" value={primaryPlan ? formatWon(primaryPlan.minimumInitialCost) : '-'} />
        <Metric icon={<LandPlot />} label="필요 재배면적" value={primaryPlan ? formatPyeong(primaryPlan.requiredArea) : '-'} />
        <Metric icon={<MapPin />} label="후보지 공공점수" value={candidate ? `${candidate.public_api_score}점` : '-'} />
        <Metric
          icon={<CheckCircle2 />}
          label="선호도 평균"
          value={`${(Object.values(preferences).reduce((sum, value) => sum + value, 0) / Object.values(preferences).length).toFixed(1)}점`}
        />
      </div>

      {analysisResult?.gemini_report && (
        <div className="glassCard aiReportCard" style={{ borderLeft: '4px solid var(--green)', display: 'grid', gap: '16px' }}>
          <div className="cardTitle" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <Sparkles size={18} style={{ color: 'var(--green)' }} />
            <span>Gemini AI 심층 입지 분석 리포트</span>
          </div>
          
          <div style={{ lineHeight: '1.65', color: 'var(--text)' }}>
            {analysisResult.gemini_report.analysis_summary}
          </div>
          
          <div className="twoColumn" style={{ marginTop: '10px', paddingTop: '16px', borderTop: '1px solid var(--line)' }}>
            <div>
              <strong style={{ display: 'block', marginBottom: '8px', color: 'var(--text)' }}>🛠️ 드론 관측 현장 결함 및 솔루션</strong>
              <ul className="cleanList" style={{ paddingLeft: '16px', display: 'grid', gap: '8px' }}>
                {analysisResult.gemini_report.risks_solutions.map((item, idx) => (
                  <li key={idx}>
                    <strong style={{ color: 'var(--text)' }}>{item.element}</strong>: {item.solution} <em style={{ fontSize: '0.8rem', color: 'var(--muted)', fontStyle: 'normal' }}>({item.cause})</em>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <strong style={{ display: 'block', marginBottom: '8px', color: 'var(--text)' }}>🚀 단계별 창농 실천 로드맵</strong>
              <ol className="cleanList" style={{ paddingLeft: '16px', display: 'grid', gap: '8px', listStyleType: 'decimal' }}>
                {analysisResult.gemini_report.startup_roadmap.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      )}

      <div className="twoColumn">
        <div className="glassCard">
          <div className="cardTitle">추천 근거</div>
          <ul className="cleanList">
            <li>현재 세후소득을 기준으로 필요한 월 순이익을 먼저 계산했습니다.</li>
            <li>지역별 판매가격, 운영비, 시설비를 반영해 최소 초기비용 조합을 선택했습니다.</li>
            <li>원본 후보지 공공데이터 점수와 개인 선호도 가중치를 함께 참고합니다.</li>
            <li>드론 분석 결과가 있으면 최종 점수에 보정 반영합니다.</li>
          </ul>
        </div>

        <div className="glassCard">
          <div className="cardTitle">리포트 내보내기</div>
          <p className="mutedText">현재 계산 조건, 후보지, 선호도, 드론 분석 결과를 JSON으로 내려받을 수 있습니다.</p>
          <button type="button" className="primaryButton" onClick={onDownload}>
            <Download size={17} />
            최종 리포트 JSON 다운로드
          </button>
        </div>
      </div>
    </section>
  );
}

function InvestmentCard({ option }) {
  return (
    <article className="investmentCard">
      <span>{option.region.name}</span>
      <strong>{option.crop.name}</strong>
      <p>{option.crop.summary}</p>
      <div>
        <b>{formatWon(option.minimumInitialCost)}</b>
        <small>초기 투자비</small>
      </div>
      <div className="miniStats">
        <span>{formatPyeong(option.requiredArea)}</span>
        <span>{formatWon(option.monthlyNetProfit)} / 월</span>
      </div>
    </article>
  );
}

function DroneResult({ result }) {
  const details = result.analysis?.drone_data ?? {};

  return (
    <div className="droneResult">
      <div className="candidateHero">
        <div>
          <span>{result.candidate_id}</span>
          <strong>{result.suitability_grade}</strong>
        </div>
        <b>{Number(result.final_startup_suitability || 0).toFixed(1)}점</b>
      </div>
      <div className="scoreList">
        <ScoreBar label="식생 건강도" value={details.vegetation_health_score} />
        <ScoreBar label="수분 균형도" value={details.moisture_balance_score} />
        <ScoreBar label="농지 정리상태" value={details.field_condition_score} />
        <ScoreBar label="배수 안전도" value={details.drainage_risk_reverse_score} />
        <ScoreBar label="시설 설치 가능성" value={details.facility_installation_score} />
      </div>
      {result.images && (
        <div className="imagePreviewGrid">
          <img src={result.images.rgb_visualized} alt="RGB 분석 결과" />
          <img src={result.images.thermal_visualized} alt="열화상 분석 결과" />
        </div>
      )}
    </div>
  );
}

function FileField({ label, file, onChange }) {
  return (
    <label className="fileField">
      <span>
        <Upload size={17} />
        {label}
      </span>
      <input type="file" accept="image/*" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
      <em>
        <ImageIcon size={16} />
        {file ? file.name : '파일 선택 또는 샘플 사용'}
      </em>
    </label>
  );
}

function NumberField({ label, value, step, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="number" min="0" step={step} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function rankCandidates(candidates, preferences) {
  const sumOfWeights =
    (preferences.infra || 0) +
    (preferences.education || 0) +
    (preferences.sea || 0) +
    (preferences.nature || 0) +
    (preferences.metropolis || 0) +
    (preferences.landPrice || 0) +
    (preferences.subsidy || 0) +
    (preferences.community || 0);

  return candidates
    .map((candidate) => {
      const weightedScoreSum =
        (preferences.infra || 0) * (candidate.pref_infra !== undefined ? candidate.pref_infra : (candidate.public_api_score ?? 70)) +
        (preferences.education || 0) * (candidate.pref_education !== undefined ? candidate.pref_education : (candidate.public_api_score ?? 70)) +
        (preferences.sea || 0) * (candidate.pref_sea !== undefined ? candidate.pref_sea : (candidate.public_api_score ?? 70)) +
        (preferences.nature || 0) * (candidate.pref_nature !== undefined ? candidate.pref_nature : (candidate.public_api_score ?? 70)) +
        (preferences.metropolis || 0) * (candidate.pref_metropolis !== undefined ? candidate.pref_metropolis : (candidate.public_api_score ?? 70)) +
        (preferences.landPrice || 0) * (candidate.pref_land_price !== undefined ? candidate.pref_land_price : (candidate.public_api_score ?? 70)) +
        (preferences.subsidy || 0) * (candidate.pref_subsidy !== undefined ? candidate.pref_subsidy : (candidate.public_api_score ?? 70)) +
        (preferences.community || 0) * (candidate.pref_community !== undefined ? candidate.pref_community : (candidate.public_api_score ?? 70));

      const preferenceScore = sumOfWeights > 0 ? weightedScoreSum / sumOfWeights : 70;
      
      // Combine public api score (50%) and user preference score (50%)
      const publicScore = candidate.public_api_score ?? 70;
      const adjustedScore = publicScore * 0.5 + preferenceScore * 0.5;

      return {
        ...candidate,
        adjustedScore: Math.min(100, Math.max(0, Math.round(adjustedScore * 10) / 10))
      };
    })
    .sort((a, b) => b.adjustedScore - a.adjustedScore);
}

function calculateFinalScore(candidate, analysisResult) {
  if (analysisResult && analysisResult.final_startup_suitability !== undefined) {
    return Number(analysisResult.final_startup_suitability);
  }
  const publicScore = Number(candidate?.public_api_score ?? 70);
  const droneScore = Number(analysisResult?.drone_analysis_score ?? publicScore);
  return publicScore * 0.55 + droneScore * 0.35 + 8;
}
