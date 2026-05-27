import { costs, crops, marketPrices, regions, settings } from '../data/agricultureData';

function byId(items) {
  return new Map(items.map((item) => [item.id, item]));
}

const cropById = byId(crops);
const regionById = byId(regions);

function getOperatingCostPerPyeong(cost, region) {
  return (
    cost.baseOperatingCostPerPyeong +
    cost.seedlingCostPerPyeong +
    cost.laborCostPerPyeong * region.laborCostIndex +
    cost.logisticsCostPerPyeong * region.logisticsCostIndex +
    cost.landRentPerPyeongYear * region.landRentIndex
  );
}

export function calculateInvestmentOption(input, price) {
  const crop = cropById.get(price.cropId);
  const region = regionById.get(price.regionId);
  const cost = costs.find((item) => item.cropId === price.cropId && item.regionId === price.regionId);

  if (!crop || !region || !cost) return null;

  const targetMonthlyIncome = Number(input.afterTaxSalary) / 12;
  const grossRevenuePerCycle = crop.yieldPerPyeong * price.salePricePerKg;
  const adjustedRevenuePerCycle = grossRevenuePerCycle * (1 - crop.defaultLossRate);
  const operatingCostPerCycle = getOperatingCostPerPyeong(cost, region);
  const netProfitPerCycle = adjustedRevenuePerCycle - operatingCostPerCycle;
  const monthlyNetProfitPerPyeong = netProfitPerCycle / crop.productionCycleMonths;

  if (!Number.isFinite(monthlyNetProfitPerPyeong) || monthlyNetProfitPerPyeong <= 0) return null;

  const requiredArea = targetMonthlyIncome / monthlyNetProfitPerPyeong;
  const monthlyRevenue = (adjustedRevenuePerCycle / crop.productionCycleMonths) * requiredArea;
  const monthlyOperatingCost = (operatingCostPerCycle / crop.productionCycleMonths) * requiredArea;
  const monthlyNetProfit = monthlyRevenue - monthlyOperatingCost;
  const facilityCost = requiredArea * cost.facilityCostPerPyeong;
  const initialOperatingCapital = monthlyOperatingCost * settings.initialOperatingCapitalMonths;
  const rentDeposit = requiredArea * cost.landRentPerPyeongYear * settings.rentDepositYears;
  const minimumInitialCost = facilityCost + cost.equipmentCostBase + initialOperatingCapital + rentDeposit;
  const climateFit = crop.fitTags.some((tag) => region.climateTags.includes(tag));

  return {
    crop,
    region,
    price,
    cost,
    targetMonthlyIncome,
    requiredArea,
    monthlyRevenue,
    monthlyOperatingCost,
    monthlyNetProfit,
    monthlyNetProfitPerPyeong,
    facilityCost,
    initialOperatingCapital,
    rentDeposit,
    minimumInitialCost,
    climateFit
  };
}

export function buildInvestmentOptions(input) {
  return marketPrices
    .filter((price) => !input.regionId || price.regionId === input.regionId)
    .map((price) => calculateInvestmentOption(input, price))
    .filter(Boolean)
    .sort((a, b) => a.minimumInitialCost - b.minimumInitialCost);
}
