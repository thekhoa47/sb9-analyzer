import { useQuery } from '@tanstack/react-query';
import { getClients } from '../endpoints/getClients';
import { URLSearchParamsInit } from '@/types/URLSearchParamsInit';

export function useClients(params: URLSearchParamsInit) {
  return useQuery({
    queryKey: ['clients', params],
    queryFn: ({ signal }) => getClients(params, signal),
  });
}
