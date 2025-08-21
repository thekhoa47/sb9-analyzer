// hooks/usePrepImage.ts
import { useMutation } from '@tanstack/react-query';
import { createPrepImageByAddress } from './../endpoints/createPrepImageByAddress';
import { MaskResult } from '@/types/MaskResult';

export function usePrepImage() {
  return useMutation<MaskResult, Error, string>({
    mutationKey: ['prep-image'],
    mutationFn: (address) => createPrepImageByAddress(address),
  });
}
