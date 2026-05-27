import regions from './regions.json';
import crops from './crops.json';
import marketPrices from './market-prices.json';
import costs from './costs.json';
import settings from './settings.json';

export { regions, crops, marketPrices, costs, settings };

export const defaultInputs = {
  afterTaxSalary: settings.defaultAfterTaxSalary,
  regionId: settings.defaultRegionId
};
