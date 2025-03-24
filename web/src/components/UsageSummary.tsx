import React, { useMemo } from 'react';
import { useUsageSummary } from '../hooks/useEvents';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  Alert,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableCell
} from './styled';

interface UsageSummaryProps {
  customerId: string;
}

const UsageSummary: React.FC<UsageSummaryProps> = ({ customerId }) => {
  // Use useMemo to stabilize date values and prevent infinite re-renders
  const { startDate, endDate } = useMemo(() => {
    const now = new Date();
    const oneMonthAgo = new Date(now);
    oneMonthAgo.setDate(now.getDate() - 30);
    
    // Format dates properly - API expects ISO format without Z suffix
    // No need to encode here as the API service will handle that
    const end = now.toISOString().replace('Z', '');
    const start = oneMonthAgo.toISOString().replace('Z', '');
    
    return { 
      startDate: start, 
      endDate: end 
    };
  }, []);
  
  const { data: usageSummary, isLoading, isError } = useUsageSummary(customerId, startDate, endDate);
  
  const formatMetricLabel = (metric: string): string => {
    switch (metric) {
      case 'api_calls':
        return 'API Calls';
      case 'data_transfer_gb':
        return 'Data Transfer (GB)';
      case 'compute_time_sec':
        return 'Compute Time (s)';
      default:
        return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };
  
  const formatMetricValue = (metric: string, value: number): string => {
    if (metric === 'data_transfer_gb') {
      return value.toFixed(2);
    }
    return value.toString();
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Summary (Last 30 Days)</CardTitle>
      </CardHeader>
      
      <CardContent>
        {isLoading && <div>Loading usage data...</div>}
        {isError && (
          <Alert variant="danger">
            Error loading usage data. Please try again.
          </Alert>
        )}
        
        {usageSummary && !isLoading && !isError && (
          Object.entries(usageSummary).length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Service</TableHeader>
                  <TableHeader>Quantity</TableHeader>
                </TableRow>
              </TableHead>
              <tbody>
                {Object.entries(usageSummary).map(([metric, value]) => (
                  <TableRow key={metric}>
                    <TableCell>{formatMetricLabel(metric)}</TableCell>
                    <TableCell>{formatMetricValue(metric, value)}</TableCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>
          ) : (
            <div>No usage data available for this period</div>
          )
        )}
      </CardContent>
    </Card>
  );
};

export default UsageSummary; 