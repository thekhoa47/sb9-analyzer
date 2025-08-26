import { configs } from '@/configs/configs';
import { ResultsPage } from '@/types/PageResults';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

const BACKEND_BASE_URL = configs.NEXT_PUBLIC_BACKEND_URL;

export async function getResults(
  query: URLSearchParamsInit,
  signal: AbortSignal
): Promise<ResultsPage> {
  const params = new URLSearchParams(query);
  const queryParams = params ? `?${params.toString()}` : '';
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/results${queryParams}`, {
      signal,
    });
    return response.json();
  } catch (error) {
    throw new Error(`Request failed: ${error}`);
  }
}
