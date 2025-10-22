import { PropertyAnalysisOut } from '@/types/PropertyAnalysis';

export async function postPropertyAnalysisFromAddress(
  address: string
): Promise<PropertyAnalysisOut> {
  const response = await fetch('/api/analyze-property-from-address', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address_in: address }),
  });

  // Try to parse JSON regardless of status
  const ct = response.headers.get('content-type') || '';
  const isJson = ct.includes('application/json');
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      (isJson && typeof body?.detail === 'string' && body.detail) ||
      (typeof body === 'string' && body) ||
      `Request failed: ${response.status} ${response.statusText}`;
    throw Object.assign(new Error(detail), { status: response.status });
  }

  return body as PropertyAnalysisOut;
}
