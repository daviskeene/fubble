import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import { UsageEvent } from '../types';

export const useRecordEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (event: UsageEvent) => api.recordEvent(event),
    onSuccess: (_, variables) => {
      // Invalidate all usage summary queries for this customer
      queryClient.invalidateQueries({ 
        queryKey: ['usageSummary', variables.customer_id] 
      });
    }
  });
};

export const useUsageSummary = (
  customerId: string, 
  startDate: string, 
  endDate: string
) => {
  return useQuery({
    queryKey: ['usageSummary', customerId, startDate, endDate],
    queryFn: () => api.getUsageSummary(customerId, startDate, endDate),
    enabled: !!customerId && !!startDate && !!endDate,
    refetchOnWindowFocus: true,
  });
}; 