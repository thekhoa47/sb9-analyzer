import { useMutation } from '@tanstack/react-query';
import { onboardNewClient } from '../endpoints/postNewClient';
import { NewClient } from '@/types/NewClient';
import { FormValues } from '@/app/admin/clients/formSchema';

export function useOnboardNewClient() {
  return useMutation<NewClient, Error, FormValues>({
    mutationKey: ['clients'],
    mutationFn: (formValues) => onboardNewClient(formValues),
  });
}
