import { useMemo, useState } from 'react';
import { ArrowRight, Building2, Sprout, Tractor } from 'lucide-react';
import { defaultInputs, regions } from './data/agricultureData';
import { buildInvestmentOptions } from './utils/calculations';
import { formatWon } from './utils/formatters';

const dashboardHref = import.meta.env.DEV ? `${import.meta.env.BASE_URL}dashboard.html` : '/dashboard';

export function Landing() {
  const [monthlyIncome, setMonthlyIncome] = useState(defaultInputs.afterTaxSalary / 12);
  const [regionId, setRegionId] = useState(defaultInputs.regionId);
  const calculationInput = {
    afterTaxSalary: Number(monthlyIncome) * 12,
    regionId
  };
  const options = useMemo(() => buildInvestmentOptions(calculationInput), [monthlyIncome, regionId]);
  const bestOption = options[0];
  const isInvalidIncome = !Number.isFinite(Number(monthlyIncome)) || Number(monthlyIncome) <= 0;
  const yearlyFarmIncome = bestOption ? bestOption.monthlyNetProfit * 12 : 0;

  return (
    <div className="landingShell">
      <header className="simpleLanding">
        <nav className="simpleTopbar">
          <div className="brand">
            <span className="brandIcon">
              <Sprout size={22} />
            </span>
            <span>농업 월소득 투자 계산기</span>
          </div>
          <a href={dashboardHref} className="navButton">
            대시보드 열기
            <ArrowRight size={16} />
          </a>
        </nav>

        <section className="incomeCompare" aria-labelledby="landing-title">
          <div className="simpleIntro">
            <p className="eyebrow">Income Replacement</p>
            <h1 id="landing-title">청년이 돌아오는 농촌</h1>
          </div>

          <div className="landingControls" aria-label="소득과 지역 입력">
            <label className="landingField">
              <span>현재 도시 생활 월소득</span>
              <input
                type="number"
                min="0"
                step="100000"
                value={monthlyIncome}
                onChange={(event) => setMonthlyIncome(event.target.value === '' ? '' : Number(event.target.value))}
              />
            </label>

            <label className="landingField">
              <span>귀농 지역</span>
              <select value={regionId} onChange={(event) => setRegionId(event.target.value)}>
                <option value="">지역 선택 안 함 · 전국 최저비용</option>
                {regions.map((region) => (
                  <option key={region.id} value={region.id}>
                    {region.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="incomeCards" aria-label="도시 생활 소득과 귀농 예상 소득 비교">
            <article className="incomeCard cityCard">
              <span className="incomeIcon">
                <Building2 size={24} />
              </span>
              <p>도시 생활</p>
              <strong>{formatWon(Number(monthlyIncome))}</strong>
              <small>세후 월소득 기준</small>
            </article>

            <article className="incomeCard farmCard">
              <span className="incomeIcon">
                <Tractor size={24} />
              </span>
              <p>귀농 예상</p>
              <strong>{isInvalidIncome ? '-' : formatWon(bestOption?.monthlyNetProfit ?? 0)}</strong>
              <small>{bestOption ? `${bestOption.region.name} · ${bestOption.crop.name}` : '계산 가능한 조합 없음'}</small>
            </article>
          </div>

          <div className="moneyHook">
            <span>
              {regionId ? '선택 지역에서 가장 저렴한 예상 귀농 초기비용' : '전국에서 가장 저렴한 예상 귀농 초기비용'}
            </span>
            <strong>{!isInvalidIncome && bestOption ? formatWon(bestOption.minimumInitialCost) : '-'}</strong>
          </div>

          <div className="landingActions simpleActions">
            <a href={dashboardHref} className="primaryCta">
              내 조건으로 계산하기
              <ArrowRight size={18} />
            </a>
            <span>{bestOption ? `연 ${formatWon(yearlyFarmIncome)} 규모의 농업 소득 시뮬레이션` : '소득과 지역을 바꿔 비교해보세요'}</span>
          </div>

          <div className="governmentSupportInfo" style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', textAlign: 'left' }}>
            <h3 style={{ color: 'var(--green)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sprout size={18} />
              최대 정부 보조금 및 융자 지원 안내
            </h3>
            
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <strong style={{ display: 'block', color: 'var(--text)', marginBottom: '4px' }}>💰 최대 정부 보조금</strong>
                <ul className="cleanList" style={{ paddingLeft: '1.5rem', color: 'var(--muted)', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  <li>① 청년농업인 영농정착지원금(만 40세 미만, 독립경영 3년 이하): <strong>합계 3,600만 원</strong> (36개월 분할 지급)</li>
                  <li>② 지자체별 소액 보조금 (기타): <strong>100만 원 ~ 500만 원</strong></li>
                </ul>
              </div>
              
              <div>
                <strong style={{ display: 'block', color: 'var(--text)', marginBottom: '4px' }}>🏦 정부 보증 융자금</strong>
                <ul className="cleanList" style={{ paddingLeft: '1.5rem', color: 'var(--muted)', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  <li>① 일반 귀농인인 경우: <strong>최대 3억 7,500만 원</strong> 한도 대출</li>
                  <li>② 만 40세 미만 '청년후계농'으로 선발된 경우: <strong>최대 5억 7,500만 원</strong> 한도 대출</li>
                </ul>
              </div>
            </div>
            <p style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--muted)' }}>
              * 초기비용 마련 시 위 지원금과 융자를 활용하면 실제 본인 부담금을 크게 낮출 수 있습니다.
            </p>
          </div>
        </section>
      </header>
    </div>
  );
}
