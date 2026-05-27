// V-World API Configuration (Optional: Paste your API Key here to enable high-res satellite & cadastral mapping)
const VWORLD_API_KEY = "";

// State Variables
let candidates = [];
let selectedCandidateId = null;
let map = null;
let markerGroup = null;
let radarChart = null;
let barChart = null;
let weightPieChart = null;
let analysisResult = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    fetchCandidates();
    setupEventListeners();
    initWeightPieChart();
    setupPreferenceSliders();
});

// Setup DOM Event Listeners
function setupEventListeners() {
    // Preference Form Submit
    const prefForm = document.getElementById('preferenceForm');
    if (prefForm) {
        prefForm.addEventListener('submit', (e) => {
            e.preventDefault();
            fetchCandidatesWithPreferences(false);
        });
    }

    // Candidate Selector Change
    document.getElementById('candidateSelect').addEventListener('change', (e) => {
        selectedCandidateId = e.target.value;
        updateRadarChart();
    });

    // File Input labels update
    const rgbInput = document.getElementById('rgbFileInput');
    const rgbFileName = document.getElementById('rgbFileName');
    rgbInput.addEventListener('change', () => {
        if (rgbInput.files.length > 0) {
            rgbFileName.textContent = rgbInput.files[0].name;
            document.getElementById('rgbLabelText').textContent = "다른 RGB 파일 선택";
        }
    });

    const thermalInput = document.getElementById('thermalFileInput');
    const thermalFileName = document.getElementById('thermalFileName');
    thermalInput.addEventListener('change', () => {
        if (thermalInput.files.length > 0) {
            thermalFileName.textContent = thermalInput.files[0].name;
            document.getElementById('thermalLabelText').textContent = "다른 열화상 파일 선택";
        }
    });

    // Drone Analysis Form Submit
    const droneForm = document.getElementById('droneForm');
    droneForm.addEventListener('submit', (e) => {
        e.preventDefault();
        runDroneAnalysis();
    });

    // JSON Download button
    document.getElementById('downloadJsonBtn').addEventListener('click', () => {
        if (analysisResult) {
            downloadJsonReport(analysisResult);
        }
    });
}

// Live text update for preference range sliders
function setupPreferenceSliders() {
    const prefKeys = ['infra', 'education', 'sea', 'nature', 'metropolis', 'land_price', 'subsidy', 'community'];
    prefKeys.forEach(key => {
        const slider = document.getElementById(`pref-${key}-slider`);
        const valSpan = document.getElementById(`val-${key}`);
        if (slider && valSpan) {
            slider.addEventListener('input', () => {
                valSpan.textContent = `${slider.value}점`;
            });
        }
    });
}

// Tab Switching Logic (Sidebar)
function switchSection(sectionId, menuItem) {
    // Toggle active menu item
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    menuItem.classList.add('active');

    // Toggle active section
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    const targetSection = document.getElementById(sectionId);
    targetSection.classList.add('active');

    // Trigger Map and Charts resize if entering specific sections
    if (sectionId === 'public-data') {
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
                if (markerGroup) {
                    map.fitBounds(markerGroup.getBounds().pad(0.2));
                }
            }
        }, 120);
    }
}

// Image Tabs Switching (RGB vs Thermal Analyzed Images)
function switchImageTab(tabContentId, tabBtn) {
    // Deactivate all image tabs
    document.querySelectorAll('.tabs-nav .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tabs-container .tabs-content').forEach(content => content.classList.remove('active'));

    // Activate selected
    tabBtn.classList.add('active');
    document.getElementById(tabContentId).classList.add('active');
}

// Fetch Candidates List from FastAPI
async function fetchCandidates() {
    return fetchCandidatesWithPreferences(true);
}

async function fetchCandidatesWithPreferences(isInitialLoad = false) {
    showLoader("공공 필지 데이터를 연동하고 개인 맞춤 선호도를 분석하고 있습니다...");
    const infraVal = document.getElementById('pref-infra-slider') ? document.getElementById('pref-infra-slider').value : 3;
    const educationVal = document.getElementById('pref-education-slider') ? document.getElementById('pref-education-slider').value : 3;
    const seaVal = document.getElementById('pref-sea-slider') ? document.getElementById('pref-sea-slider').value : 3;
    const natureVal = document.getElementById('pref-nature-slider') ? document.getElementById('pref-nature-slider').value : 3;
    const metropolisVal = document.getElementById('pref-metropolis-slider') ? document.getElementById('pref-metropolis-slider').value : 3;
    const landPriceVal = document.getElementById('pref-land_price-slider') ? document.getElementById('pref-land_price-slider').value : 3;
    const subsidyVal = document.getElementById('pref-subsidy-slider') ? document.getElementById('pref-subsidy-slider').value : 3;
    const communityVal = document.getElementById('pref-community-slider') ? document.getElementById('pref-community-slider').value : 3;
    
    const queryParams = new URLSearchParams({
        infra: infraVal,
        education: educationVal,
        sea: seaVal,
        nature: natureVal,
        metropolis: metropolisVal,
        land_price: landPriceVal,
        subsidy: subsidyVal,
        community: communityVal
    });
    
    try {
        const response = await fetch(`/api/candidates?${queryParams.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch candidates");
        
        candidates = await response.json();
        
        // Populate UI
        populateCandidatesTable(candidates);
        populateCandidateSelect(candidates);
        
        // Set default selected
        if (candidates.length > 0) {
            selectedCandidateId = candidates[0].candidate_id;
            updateRadarChart();
            initLeafletMap(candidates);
        }
        
        // Update summary metrics
        document.getElementById('total-candidates').textContent = `${candidates.length} 곳`;
        
        const avgScore = candidates.reduce((sum, c) => sum + (c.personal_preference_score !== undefined ? c.personal_preference_score : c.public_api_score), 0) / candidates.length;
        document.getElementById('avg-public-score').textContent = `${avgScore.toFixed(1)} 점`;
        
        const excellentCount = candidates.filter(c => (c.personal_preference_score !== undefined ? c.personal_preference_score : c.public_api_score) >= 80).length;
        document.getElementById('excellent-candidates').textContent = `${excellentCount} 곳`;
        
        // Navigate to Section 2 (1차 농지 후보) if it's not the initial page load
        if (!isInitialLoad) {
            const menuItems = document.querySelectorAll('.menu-item');
            if (menuItems.length > 1) {
                switchSection('public-data', menuItems[1]);
            }
        }

    } catch (error) {
        console.error("Error fetching candidates:", error);
        alert("농지 후보지 데이터를 받아오는 데 실패했습니다.");
    } finally {
        hideLoader();
    }
}

// Populate Candidates Table
function populateCandidatesTable(data) {
    const tbody = document.querySelector('#candidatesTable tbody');
    tbody.innerHTML = '';
    
    data.forEach(c => {
        const tr = document.createElement('tr');
        tr.dataset.id = c.candidate_id;
        
        // Rating class badge
        let badgeClass = 'badge-good';
        let gradeText = '검토 가능';
        const score = c.personal_preference_score !== undefined ? c.personal_preference_score : c.public_api_score;
        if (score >= 80) {
            badgeClass = 'badge-excellent';
            gradeText = '우수';
        } else if (score < 65) {
            badgeClass = 'badge-poor';
            gradeText = '보완 필요';
        }
        
        tr.innerHTML = `
            <td><strong>${c.candidate_id}</strong></td>
            <td>${c.region}</td>
            <td>${c.address}</td>
            <td>${c.land_type}</td>
            <td>${c.area_m2.toLocaleString()} ㎡</td>
            <td style="font-weight: 500; color: #888;">${c.public_api_score.toFixed(1)} 점</td>
            <td style="font-weight: 700; color: #fff;">${score.toFixed(1)} 점</td>
            <td><span class="badge ${badgeClass}">${gradeText}</span></td>
        `;
        
        // Click row to select
        tr.addEventListener('click', () => {
            selectedCandidateId = c.candidate_id;
            document.getElementById('candidateSelect').value = c.candidate_id;
            updateRadarChart();
            
            // Pan map to clicked marker
            if (map) {
                map.panTo([c.lat, c.lng]);
            }
        });
        
        tbody.appendChild(tr);
    });
}

// Populate Candidate Select Dropdown
function populateCandidateSelect(data) {
    const select = document.getElementById('candidateSelect');
    select.innerHTML = '';
    
    data.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.candidate_id;
        opt.textContent = `${c.candidate_id} - ${c.address}`;
        select.appendChild(opt);
    });
}

// Initialize Leaflet Map
function initLeafletMap(data) {
    if (map !== null) {
        if (markerGroup) {
            markerGroup.clearLayers();
            data.forEach(c => {
                const score = c.personal_preference_score !== undefined ? c.personal_preference_score : c.public_api_score;
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
                    <div style="color: #0b0f19; font-family: 'Noto Sans KR'; font-size: 0.85rem;">
                        <strong>${c.candidate_id}</strong><br>
                        <span style="font-size:0.75rem; color:#555;">${c.address}</span><br>
                        <strong>공공 스코어: ${c.public_api_score}점</strong><br>
                        <strong>맞춤 스코어: ${score}점</strong>
                    </div>
                `);
                
                marker.on('click', () => {
                    selectedCandidateId = c.candidate_id;
                    document.getElementById('candidateSelect').value = c.candidate_id;
                    updateRadarChart();
                });
            });
            map.fitBounds(markerGroup.getBounds().pad(0.2));
        }
        return;
    }
    
    // Calculate center
    const lats = data.map(c => c.lat);
    const lngs = data.map(c => c.lng);
    const centerLat = lats.reduce((a,b)=>a+b, 0) / lats.length;
    const centerLng = lngs.reduce((a,b)=>a+b, 0) / lngs.length;
    
    // Init Leaflet Map
    map = L.map('map').setView([centerLat, centerLng], 7);
    
    // Base Layers
    const cartoLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    });
    
    let baseMaps = {
        "기본 다크/라이트 맵": cartoLight
    };
    let overlayMaps = {};
    
    if (typeof VWORLD_API_KEY !== 'undefined' && VWORLD_API_KEY && VWORLD_API_KEY.trim() !== "") {
        const vworldBase = L.tileLayer(`https://api.vworld.kr/req/wmts/1.0.0/${VWORLD_API_KEY}/Base/{z}/{y}/{x}.png`, {
            maxZoom: 19,
            attribution: '© V-World Base'
        });
        
        const vworldSatellite = L.tileLayer(`https://api.vworld.kr/req/wmts/1.0.0/${VWORLD_API_KEY}/Satellite/{z}/{y}/{x}.jpeg`, {
            maxZoom: 19,
            attribution: '© V-World Satellite'
        });
        
        const cadastralLayer = L.tileLayer.wms('https://api.vworld.kr/req/wms', {
            layers: 'LP_PA_CBND_BUBUN',
            styles: 'LP_PA_CBND_BUBUN',
            format: 'image/png',
            transparent: true,
            version: '1.3.0',
            apiKey: VWORLD_API_KEY,
            attribution: '© V-World 지적도'
        });
        
        const agriZoneLayer = L.tileLayer.wms('https://api.vworld.kr/req/wms', {
            layers: 'LT_C_UQ111',
            styles: 'LT_C_UQ111',
            format: 'image/png',
            transparent: true,
            version: '1.3.0',
            apiKey: VWORLD_API_KEY,
            attribution: '© V-World 농업진흥지역'
        });
        
        // Add default V-World Base Map
        vworldBase.addTo(map);
        
        baseMaps["브이월드 도로지도"] = vworldBase;
        baseMaps["브이월드 위성지도"] = vworldSatellite;
        
        overlayMaps["연속지적도 경계"] = cadastralLayer;
        overlayMaps["농업진흥지역 구역"] = agriZoneLayer;
        
        L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(map);
    } else {
        cartoLight.addTo(map);
    }
    
    markerGroup = L.featureGroup().addTo(map);
    
    data.forEach(c => {
        const score = c.personal_preference_score !== undefined ? c.personal_preference_score : c.public_api_score;
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
            <div style="color: #0b0f19; font-family: 'Noto Sans KR'; font-size: 0.85rem;">
                <strong>${c.candidate_id}</strong><br>
                <span style="font-size:0.75rem; color:#555;">${c.address}</span><br>
                <strong>공공 스코어: ${c.public_api_score}점</strong><br>
                <strong>맞춤 스코어: ${score}점</strong>
            </div>
        `);
        
        marker.on('click', () => {
            selectedCandidateId = c.candidate_id;
            document.getElementById('candidateSelect').value = c.candidate_id;
            updateRadarChart();
        });
    });
    
    // Fit map bounds
    map.fitBounds(markerGroup.getBounds().pad(0.2));
}

// Update Radar Chart (Chart.js)
function updateRadarChart() {
    const candidate = candidates.find(c => c.candidate_id === selectedCandidateId);
    if (!candidate) return;
    
    const chartData = [
        candidate.soil_crop_score,
        candidate.agricultural_zone_score,
        candidate.actual_farmland_score,
        candidate.accessibility_score,
        candidate.drainage_slope_score,
        candidate.geo_environment_score,
        candidate.youth_policy_score
    ];
    
    if (radarChart) {
        radarChart.data.datasets[0].data = chartData;
        radarChart.data.datasets[0].label = `${candidate.candidate_id} 점수 구성`;
        radarChart.update();
    } else {
        const ctx = document.getElementById('radarChart').getContext('2d');
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['토양적성', '농업진흥구역', '실제농경지', '접근성', '배수/경사', '지질환경', '청년정책'],
                datasets: [{
                    label: `${candidate.candidate_id} 점수 구성`,
                    data: chartData,
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10b981',
                    borderWidth: 2,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        pointLabels: { color: '#9ca3af', font: { family: 'Outfit', size: 10 } },
                        ticks: { color: '#9ca3af', backdropColor: 'transparent', stepSize: 20 },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Run Drone Image Analysis API
async function runDroneAnalysis() {
    if (!selectedCandidateId) {
        alert("먼저 분석 대상 농지를 선택하세요.");
        return;
    }

    const rgbInput = document.getElementById('rgbFileInput');
    const thermalInput = document.getElementById('thermalFileInput');
    const useSample = document.getElementById('useSampleCheck').checked;

    if (!useSample && (rgbInput.files.length === 0 || thermalInput.files.length === 0)) {
        alert("드론 RGB 및 열화상 파일을 모두 업로드하거나, 샘플 대체 모드를 체크해 주세요.");
        return;
    }

    showLoader("드론 원격 비행 매핑 영상을 분석하여 식생 밀도 검출 및 지표 열전도를 모델링하고 있습니다...");

    const formData = new FormData();
    formData.append('candidate_id', selectedCandidateId);
    formData.append('use_sample', useSample);
    
    // Append preference slider values
    formData.append('infra', document.getElementById('pref-infra-slider') ? document.getElementById('pref-infra-slider').value : 3);
    formData.append('education', document.getElementById('pref-education-slider') ? document.getElementById('pref-education-slider').value : 3);
    formData.append('sea', document.getElementById('pref-sea-slider') ? document.getElementById('pref-sea-slider').value : 3);
    formData.append('nature', document.getElementById('pref-nature-slider') ? document.getElementById('pref-nature-slider').value : 3);
    formData.append('metropolis', document.getElementById('pref-metropolis-slider') ? document.getElementById('pref-metropolis-slider').value : 3);
    formData.append('land_price', document.getElementById('pref-land_price-slider') ? document.getElementById('pref-land_price-slider').value : 3);
    formData.append('subsidy', document.getElementById('pref-subsidy-slider') ? document.getElementById('pref-subsidy-slider').value : 3);
    formData.append('community', document.getElementById('pref-community-slider') ? document.getElementById('pref-community-slider').value : 3);
    
    if (rgbInput.files.length > 0) {
        formData.append('rgb_file', rgbInput.files[0]);
    }
    if (thermalInput.files.length > 0) {
        formData.append('thermal_file', thermalInput.files[0]);
    }

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("API analysis failed");
        
        analysisResult = await response.json();
        
        // Show result panel, hide warning
        document.getElementById('analysis-results-container').style.display = 'block';
        document.getElementById('analysis-warning').style.display = 'none';
        
        // Update metric scores
        document.getElementById('drone-overall-score').textContent = `${analysisResult.drone_analysis_score.toFixed(1)} 점`;
        
        const details = analysisResult.analysis.drone_data;
        document.getElementById('metric-veg-val').textContent = `${details.vegetation_health_score}점`;
        document.getElementById('metric-moist-val').textContent = `${details.moisture_balance_score}점`;
        document.getElementById('metric-cond-val').textContent = `${details.field_condition_score}점`;
        document.getElementById('metric-drainage-val').textContent = `${details.drainage_risk_reverse_score}점`;
        document.getElementById('metric-facility-val').textContent = `${details.facility_installation_score}점`;
        document.getElementById('metric-difficulty-val').textContent = `${details.management_difficulty_score}점 (낮음)`;

        // Update image tags
        document.getElementById('rgb-orig-img').src = analysisResult.images.rgb_original;
        document.getElementById('rgb-vis-img').src = analysisResult.images.rgb_visualized;
        document.getElementById('thermal-orig-img').src = analysisResult.images.thermal_original;
        document.getElementById('thermal-vis-img').src = analysisResult.images.thermal_visualized;

        // Render Bar Chart for Drone details
        updateDroneBarChart(details);
        
        // Enable Final Recommendation Panel
        setupFinalRecommendation(analysisResult);

    } catch (error) {
        console.error("Analysis Error:", error);
        alert("드론 이미지 분석 API 호출에 실패했습니다.");
    } finally {
        hideLoader();
    }
}

// Render Drone Bar Chart
function updateDroneBarChart(details) {
    const labels = ["식생 건강도", "수분 균형도", "농지 정리상태", "배수 안전도", "시설 설치용이성", "관리 용이성"];
    const chartData = [
        details.vegetation_health_score,
        details.moisture_balance_score,
        details.field_condition_score,
        details.drainage_risk_reverse_score,
        details.facility_installation_score,
        details.management_difficulty_reverse_score
    ];

    if (barChart) {
        barChart.data.datasets[0].data = chartData;
        barChart.update();
    } else {
        const ctx = document.getElementById('barChart').getContext('2d');
        barChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: chartData,
                    backgroundColor: 'rgba(16, 185, 129, 0.4)',
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.06)' },
                        ticks: { color: '#9ca3af' },
                        suggestedMax: 100
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Final Recommendation Logic
function setupFinalRecommendation(result) {
    // Show container
    document.getElementById('final-result-container').style.display = 'block';
    document.getElementById('final-result-warning').style.display = 'none';

    // Banner Text
    const grade = result.suitability_grade;
    const banner = document.getElementById('resultBanner');
    const gradeText = document.getElementById('resultGradeText');
    const summaryText = document.getElementById('resultSummaryText');
    
    gradeText.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${result.candidate_id} 입지 진단 등급: [ ${grade} ]`;
    summaryText.textContent = result.analysis_summary;

    // Apply color class to Banner
    banner.className = 'result-banner';
    if (grade === "매우 적합" || grade === "적합") {
        banner.style.borderLeft = "6px solid #10b981";
    } else if (grade === "조건부 적합") {
        banner.style.borderLeft = "6px solid #f59e0b";
    } else {
        banner.style.borderLeft = "6px solid #ef4444";
    }

    // Metric numbers
    document.getElementById('final-overall-score').textContent = `${result.final_startup_suitability.toFixed(1)} 점`;
    document.getElementById('final-public-score').textContent = `${result.public_api_score.toFixed(1)} 점`;
    document.getElementById('final-pref-score').textContent = `${(result.personal_preference_score !== undefined ? result.personal_preference_score : 0).toFixed(1)} 점`;
    document.getElementById('final-drone-score').textContent = `${result.drone_analysis_score.toFixed(1)} 점`;
    document.getElementById('final-policy-score').textContent = `${result.analysis.public_data.youth_policy_score.toFixed(1)} 점`;

    // Crops mapping
    const cropContainer = document.getElementById('cropListContainer');
    cropContainer.innerHTML = '';
    result.recommended_crops.forEach(crop => {
        const item = document.createElement('div');
        item.className = 'alert-box alert-success';
        item.innerHTML = `<i class="fa-solid fa-seedling" style="margin-top: 3px;"></i><div><strong>${crop}</strong></div>`;
        cropContainer.appendChild(item);
    });

    // Risks mapping
    const riskContainer = document.getElementById('riskListContainer');
    riskContainer.innerHTML = '';
    result.risks.forEach(risk => {
        const item = document.createElement('div');
        item.className = 'alert-box alert-warning';
        item.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="margin-top: 3px;"></i><div>${risk}</div>`;
        riskContainer.appendChild(item);
    });

    // Policies mapping
    const policyContainer = document.getElementById('policyListContainer');
    policyContainer.innerHTML = '';
    result.policy_recommendations.forEach(policy => {
        const item = document.createElement('div');
        item.className = 'alert-box alert-info';
        item.innerHTML = `<i class="fa-solid fa-landmark" style="margin-top: 3px;"></i><div>${policy}</div>`;
        policyContainer.appendChild(item);
    });
}

// Initial Weights Pie Chart
function initWeightPieChart() {
    const ctx = document.getElementById('weightPieChart').getContext('2d');
    weightPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ["1차 공공데이터 (40%)", "개인 선호 맞춤 (20%)", "2차 드론 분석 (25%)", "청년 정책 지원 (15%)"],
            datasets: [{
                data: [40, 20, 25, 15],
                backgroundColor: [
                    '#10b981',
                    '#06b6d4',
                    '#3b82f6',
                    '#f59e0b'
                ],
                borderColor: '#0b0f19',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9ca3af', font: { family: 'Outfit', size: 9 } }
                }
            },
            cutout: '60%'
        }
    });
}

// Download JSON helper
function downloadJsonReport(data) {
    // Remove Base64 images to keep the JSON file size small and clean
    const cleanData = JSON.parse(JSON.stringify(data));
    delete cleanData.images; // Delete the images property

    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(cleanData, null, 2))}`;
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", jsonString);
    downloadAnchor.setAttribute("download", `AgriYouth_Diagnosis_Report_${cleanData.candidate_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
}

// Loading UI Controls
function showLoader(text = "작업을 실행 중입니다...") {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoader() {
    document.getElementById('loadingOverlay').classList.remove('active');
}
