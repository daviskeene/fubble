import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import { Subscription } from '../types';

export const useSubscriptions = (customerId: string) => {
  return useQuery({
    queryKey: ['subscriptions', customerId],
    queryFn: () => api.getSubscriptions(customerId),
    enabled: !!customerId
  });
};

export const useCreateSubscription = (customerId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (subscription: Subscription) => api.createSubscription(customerId, subscription),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions', customerId] });
    }
  });
}; 