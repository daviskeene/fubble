import React, { useState } from 'react';
import { UsageEvent } from '../types';
import { useRecordEvent } from '../hooks/useEvents';
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

const EventForm: React.FC<EventFormProps> = ({ customerId, onEventRecorded }) => {
  const [metric, setMetric] = useState('api_calls');
  const [quantity, setQuantity] = useState('1');
  const [properties, setProperties] = useState<Record<string, any>>({});
  const [showSuccess, setShowSuccess] = useState(false);
  
  const { mutate: recordEvent, isPending } = useRecordEvent();
  
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
  
  // Define metric options for the demo
  const metricOptions = [
    { value: 'api_calls', label: 'API Calls' },
    { value: 'data_transfer_gb', label: 'Data Transfer (GB)' },
    { value: 'compute_time_sec', label: 'Compute Time (seconds)' }
  ];
  
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
        
        <form onSubmit={handleSubmit}>
          <FormGroup>
            <Label>Metric</Label>
            <Select 
              value={metric} 
              onChange={(e) => setMetric(e.target.value)}
            >
              {metricOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </FormGroup>
          
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
        </form>
      </CardContent>
    </Card>
  );
};

export default EventForm; 