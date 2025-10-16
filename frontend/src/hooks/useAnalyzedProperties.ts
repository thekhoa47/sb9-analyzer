import { useQuery } from '@tanstack/react-query';
import { getAnalyzedProperties } from '../endpoints/getAnalyzedProperties';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

export function useAnalyzedProperties(params: URLSearchParamsInit) {
  return useQuery({
    queryKey: ['results', params],
    queryFn: ({ signal }) => getAnalyzedProperties(params, signal),
  });
}
