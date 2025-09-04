import { configs } from '@/configs/configs';
import { PaginatedClients } from '@/types/NewClient';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

const BACKEND_BASE_URL = configs.NEXT_PUBLIC_BACKEND_URL;

export async function getClients(
  query: URLSearchParamsInit,
  signal: AbortSignal
): Promise<PaginatedClients> {
  const params = new URLSearchParams(query);
  const queryParams = params ? `?${params.toString()}` : '';
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/clients${queryParams}`, {
      signal,
    });
    return response.json();
  } catch (error) {
    throw new Error(`Request failed: ${error}`);
  }
}
