import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import { Plan } from '../types';

export const usePlans = () => {
  return useQuery({
    queryKey: ['plans'],
    queryFn: api.getPlans
  });
};

export const usePlan = (id: string) => {
  return useQuery({
    queryKey: ['plans', id],
    queryFn: () => api.getPlan(id),
    enabled: !!id
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