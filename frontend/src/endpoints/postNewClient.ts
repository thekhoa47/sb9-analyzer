import { FormValues } from '@/app/admin/clients/formSchema';
import { configs } from '@/configs/configs';
import { NewClient } from '@/types/NewClient';

export async function onboardNewClient(payload: FormValues): Promise<NewClient> {
  const response = await fetch(`${configs.NEXT_PUBLIC_BACKEND_URL}/clients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
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

  return body as NewClient;
}
