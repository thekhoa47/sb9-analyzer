import { useMutation } from '@tanstack/react-query';
import { onboardNewClient } from '../endpoints/postNewClient';
import { NewClient } from '@/types/NewClient';
import { FormValues } from '@/app/admin/clients/formSchema';

export function useOnboardNewClient() {
  return useMutation<NewClient, Error, FormValues>({
    mutationKey: ['onboard-new-client'],
    mutationFn: (formValues) => onboardNewClient(formValues),
  });
}
