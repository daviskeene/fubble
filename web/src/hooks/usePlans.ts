import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import { Plan } from '../types';

export const usePlans = (activeOnly: boolean = true) => {
  return useQuery<Plan[]>({
    queryKey: ['plans', { activeOnly }],
    queryFn: () => api.getPlans(activeOnly),
    refetchOnWindowFocus: true
  });
};

export const usePlan = (planId: string) => {
  return useQuery<Plan>({
    queryKey: ['plan', planId],
    queryFn: () => api.getPlan(planId),
    enabled: !!planId
  });
};

export const useCustomerPlan = (customerId: string) => {
  return useQuery<{ 
    subscription_id: string;
    plan: Plan;
    subscription: any;
  } | null>({
    queryKey: ['customerPlan', customerId],
    queryFn: () => api.getCustomerPlan(customerId),
    enabled: !!customerId,
    refetchOnWindowFocus: true
  });
};

export const useCreatePlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (plan: Plan) => api.createPlan(plan),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
    }
  });
}; 