export function formatNumberWithCommas(value: number | string) {
  if (value === null || value === undefined || value === '') return '';
  const num = typeof value === 'number' ? value : Number(value.replace(/,/g, ''));
  if (isNaN(num)) return '';
  return num.toLocaleString('en-US');
}
