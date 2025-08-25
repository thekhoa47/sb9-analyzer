import { useMutation } from '@tanstack/react-query';
import { postSb9AnalyzeByAddress } from '../endpoints/postSb9AnalyzeByAddress';
import { AnalyzeResult } from '@/types/MaskResult';

export function useAnalyze() {
  return useMutation<AnalyzeResult, Error, string>({
    mutationKey: ['analyze'],
    mutationFn: (address) => postSb9AnalyzeByAddress(address),
  });
}
