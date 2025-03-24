import React, { useState, useEffect } from 'react';
import { UsageEvent, PriceComponent } from '../types';
import { useRecordEvent } from '../hooks/useEvents';
import { useCustomerPlan } from '../hooks/usePlans';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent, 
  CardFooter, 
  FormGroup, 
  Label, 
  Input, 
  Select, 
  Button,
  Alert
} from './styled';

interface EventFormProps {
  customerId: string;
  onEventRecorded?: () => void;
}

// Define the full metric options map for reference and display names
const ALL_METRIC_OPTIONS: { [key: string]: string } = {
  'api_calls': 'API Calls',
  'data_transfer_gb': 'Data Transfer (GB)',
  'compute_time_sec': 'Compute Time (seconds)',
  'subscription_fee': 'Subscription Fee'
};

const EventForm: React.FC<EventFormProps> = ({ customerId, onEventRecorded }) => {
  const [metric, setMetric] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [properties, setProperties] = useState<Record<string, any>>({});
  const [showSuccess, setShowSuccess] = useState(false);
  const [metricOptions, setMetricOptions] = useState<Array<{value: string, label: string}>>([]);
  
  // Fetch the customer's plan
  const { data: planData, isLoading: isPlanLoading } = useCustomerPlan(customerId);
  const { mutate: recordEvent, isPending } = useRecordEvent();
  
  // Extract metric options from the customer's plan price components
  useEffect(() => {
    if (planData && planData.plan && planData.plan.price_components) {
      // Extract unique metric names from price components
      const metrics = planData.plan.price_components
        .filter((component: PriceComponent) => component.pricing_type !== 'subscription')
        .map((component: PriceComponent) => ({
          value: component.metric_name,
          label: component.display_name || 
                 (ALL_METRIC_OPTIONS.hasOwnProperty(component.metric_name) ? 
                  ALL_METRIC_OPTIONS[component.metric_name as keyof typeof ALL_METRIC_OPTIONS] : 
                  component.metric_name)
        }));
      
      setMetricOptions(metrics);
      
      // Set the first metric as default if available and current metric is not in the options
      if (metrics.length > 0 && (!metric || !metrics.some(m => m.value === metric))) {
        setMetric(metrics[0].value);
      }
    }
  }, [planData, metric]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Create a new usage event
    const event: UsageEvent = {
      customer_id: customerId,
      metric_name: metric,
      quantity: Number(quantity),
      properties
    };
    
    // Record the event
    recordEvent(event, {
      onSuccess: () => {
        setShowSuccess(true);
        
        // Hide success message after 3 seconds
        setTimeout(() => setShowSuccess(false), 3000);
        
        // Call the callback if provided
        if (onEventRecorded) {
          onEventRecorded();
        }
      }
    });
  };
  
  // Define property fields based on selected metric
  const renderPropertyFields = () => {
    switch (metric) {
      case 'api_calls':
        return (
          <>
            <FormGroup>
              <Label>Endpoint</Label>
              <Select 
                value={properties.endpoint || ''} 
                onChange={(e) => setProperties({ ...properties, endpoint: e.target.value })}
              >
                <option value="">Select endpoint</option>
                <option value="/users">/users</option>
                <option value="/products">/products</option>
                <option value="/orders">/orders</option>
                <option value="/search">/search</option>
                <option value="/analytics">/analytics</option>
              </Select>
            </FormGroup>
            <FormGroup>
              <Label>Method</Label>
              <Select 
                value={properties.method || ''} 
                onChange={(e) => setProperties({ ...properties, method: e.target.value })}
              >
                <option value="">Select method</option>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </Select>
            </FormGroup>
          </>
        );
        
      case 'data_transfer_gb':
        return (
          <FormGroup>
            <Label>Compression</Label>
            <Select 
              value={properties.compression || ''} 
              onChange={(e) => setProperties({ ...properties, compression: e.target.value })}
            >
              <option value="">Select compression</option>
              <option value="none">None</option>
              <option value="gzip">gzip</option>
              <option value="brotli">brotli</option>
            </Select>
          </FormGroup>
        );
        
      case 'compute_time_sec':
        return (
          <FormGroup>
            <Label>Job Type</Label>
            <Select 
              value={properties.job_type || ''} 
              onChange={(e) => setProperties({ ...properties, job_type: e.target.value })}
            >
              <option value="">Select job type</option>
              <option value="data_processing">Data Processing</option>
              <option value="report_generation">Report Generation</option>
              <option value="ai_model_training">AI Model Training</option>
            </Select>
          </FormGroup>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Record Usage Event</CardTitle>
      </CardHeader>
      
      <CardContent>
        {showSuccess && (
          <Alert variant="success">
            Event recorded successfully!
          </Alert>
        )}
        
        {isPlanLoading ? (
          <div>Loading plan information...</div>
        ) : metricOptions.length === 0 ? (
          <Alert variant="info">
            No billable metrics available in the current plan.
          </Alert>
        ) : (
          <form onSubmit={handleSubmit}>
            <FormGroup>
              <Label>Metric</Label>
              <Select 
                value={metric} 
                onChange={(e) => {
                  setMetric(e.target.value);
                  setProperties({}); // Reset properties when metric changes
                }}
              >
                {!metric && <option value="">Select a metric</option>}
                {metricOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormGroup>
            
            {metric && (
              <>
                <FormGroup>
                  <Label>Quantity</Label>
                  <Input 
                    type="number" 
                    value={quantity} 
                    onChange={(e) => setQuantity(e.target.value)}
                    min="0" 
                    step={metric === 'data_transfer_gb' ? '0.01' : '1'}
                    required
                  />
                </FormGroup>
                
                {renderPropertyFields()}
                
                <CardFooter>
                  <Button type="submit" disabled={isPending}>
                    {isPending ? 'Recording...' : 'Record Event'}
                  </Button>
                </CardFooter>
              </>
            )}
          </form>
        )}
      </CardContent>
    </Card>
  );
};

export default EventForm; 