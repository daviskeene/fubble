import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';

export const useInvoices = () => {
  return useQuery({
    queryKey: ['invoices'],
    queryFn: api.getInvoices,
    refetchOnWindowFocus: true,
    refetchInterval: 30000 // Refetch every 30 seconds
  });
};

export const useCustomerInvoices = (customerId: string) => {
  return useQuery({
    queryKey: ['customerInvoices', customerId],
    queryFn: () => api.getCustomerInvoices(customerId),
    enabled: !!customerId,
    refetchOnWindowFocus: true,
    refetchInterval: 30000 // Refetch every 30 seconds
  });
};

export const useInvoice = (invoiceId: string) => {
  return useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: () => api.getInvoice(invoiceId),
    enabled: !!invoiceId
  });
};

export const useGenerateInvoices = (customerId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ startDate, endDate }: { startDate: string; endDate: string }) => 
      api.generateInvoices(startDate, endDate, customerId),
    onSuccess: () => {
      // Invalidate all invoice-related queries to ensure real-time updates
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ 
        queryKey: ['customerInvoices'] 
      });
    }
  });
}; 