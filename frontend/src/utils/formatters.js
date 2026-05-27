export function formatWon(value) {
  if (!Number.isFinite(value)) return '-';
  const abs = Math.abs(value);
  if (abs >= 100000000) return `${(value / 100000000).toFixed(1)}억 원`;
  if (abs >= 10000) return `${Math.round(value / 10000).toLocaleString('ko-KR')}만 원`;
  return `${Math.round(value).toLocaleString('ko-KR')}원`;
}

export function formatPyeong(value) {
  if (!Number.isFinite(value)) return '-';
  return `약 ${Math.ceil(value).toLocaleString('ko-KR')}평`;
}

export function formatNumber(value, digits = 1) {
  if (!Number.isFinite(value)) return '-';
  return value.toLocaleString('ko-KR', {
    maximumFractionDigits: digits
  });
}
