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
                onChange={(event) => setMonthlyIncome(Number(event.target.value))}
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
        </section>
      </header>
    </div>
  );
}
