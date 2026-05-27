import { Banknote, BarChart3, LandPlot, MapPin, Package } from 'lucide-react';
import { formatPyeong, formatWon } from '../utils/formatters';

export function RecommendationCard({ label, tone, plan }) {
  return (
    <article className={`recommendation ${tone}`}>
      <div className="cardHeader">
        <span>{label}</span>
        <strong>{plan.region.name} · {plan.crop.name}</strong>
      </div>
      <p>{plan.crop.summary}</p>

      <div className="statRows">
        <div>
          <Banknote size={17} />
          <span>최소 초기비용</span>
          <strong>{formatWon(plan.minimumInitialCost)}</strong>
        </div>
        <div>
          <LandPlot size={17} />
          <span>필요 재배면적</span>
          <strong>{formatPyeong(plan.requiredArea)}</strong>
        </div>
        <div>
          <BarChart3 size={17} />
          <span>예상 월 순이익</span>
          <strong>{formatWon(plan.monthlyNetProfit)}</strong>
        </div>
        <div>
          <Package size={17} />
          <span>판매 단가</span>
          <strong>{formatWon(plan.price.salePricePerKg)} / kg</strong>
        </div>
        <div>
          <MapPin size={17} />
          <span>판매 채널</span>
          <strong>{plan.price.salesChannel}</strong>
        </div>
      </div>

      <div className="riskLine">
        {plan.crop.type} · 노동 강도 {plan.crop.laborIntensity} · 지역 리스크: {plan.region.risks.join(', ')}
      </div>
    </article>
  );
}
