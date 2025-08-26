import { useQuery } from '@tanstack/react-query';
import { getResults } from '../endpoints/getResults';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

export function useResult(params: URLSearchParamsInit) {
  return useQuery({
    queryKey: ['results', params],
    queryFn: ({ signal }) => getResults(params, signal),
  });
}
