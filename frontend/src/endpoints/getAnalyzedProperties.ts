import { configs } from '@/configs/configs';
import { AnalyzedPropertiesPage } from '@/types/PropertyAnalysis';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

const BACKEND_BASE_URL = configs.NEXT_PUBLIC_BACKEND_URL;

export async function getAnalyzedProperties(
  query: URLSearchParamsInit,
  signal: AbortSignal
): Promise<AnalyzedPropertiesPage> {
  const params = new URLSearchParams(query);
  const queryParams = params ? `?${params.toString()}` : '';
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/analyzed-properties${queryParams}`, {
      signal,
    });
    return response.json();
  } catch (error) {
    throw new Error(`Request failed: ${error}`);
  }
}
