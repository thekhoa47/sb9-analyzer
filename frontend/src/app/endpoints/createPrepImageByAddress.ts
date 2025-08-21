import { configs } from '@/configs/configs';
import { MaskResult } from '@/types/MaskResult';

const BACKEND_BASE_URL = configs.NEXT_PUBLIC_BACKEND_URL;

export async function createPrepImageByAddress(address: string): Promise<MaskResult> {
  const response = await fetch(`${BACKEND_BASE_URL}/prep-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address }),
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

  return body as MaskResult;
}