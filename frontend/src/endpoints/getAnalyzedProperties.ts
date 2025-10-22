import { AnalyzedPropertiesPage } from '@/types/PropertyAnalysis';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

export async function getAnalyzedProperties(
  query: URLSearchParamsInit,
  signal: AbortSignal
): Promise<AnalyzedPropertiesPage> {
  const params = new URLSearchParams(query);
  const queryParams = params ? `?${params.toString()}` : '';
  try {
    const response = await fetch(`/api/analyzed-properties${queryParams}`, {
      signal,
    });
    return response.json();
  } catch (error) {
    throw new Error(`Request failed: ${error}`);
  }
}
