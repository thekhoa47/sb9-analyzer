import { useMutation } from '@tanstack/react-query';
import { postPropertyAnalysisFromAddress } from '../endpoints/postPropertyAnalysisFromAddress';
import { PropertyAnalysisOut } from '@/types/PropertyAnalysis';

export function usePropertyAnalysisFromAddress() {
  return useMutation<PropertyAnalysisOut, Error, string>({
    mutationKey: ['analyze'],
    mutationFn: (address) => postPropertyAnalysisFromAddress(address),
  });
}
