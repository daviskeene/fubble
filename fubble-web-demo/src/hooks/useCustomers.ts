import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import { Customer } from '../types';

export const useCustomers = () => {
  return useQuery({
    queryKey: ['customers'],
    queryFn: api.getCustomers
  });
};

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ['customers', id],
    queryFn: () => api.getCustomer(id),
    enabled: !!id
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (customer: Customer) => api.createCustomer(customer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    }
  });
}; 