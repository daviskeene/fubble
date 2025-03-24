import React from 'react';
import { useCustomers } from '../hooks/useCustomers';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent, 
  Select,
  FormGroup,
  Label,
  Alert
} from './styled';

interface CustomerSelectProps {
  selectedCustomerId: string;
  onSelectCustomer: (customerId: string) => void;
}

const CustomerSelect: React.FC<CustomerSelectProps> = ({ 
  selectedCustomerId, 
  onSelectCustomer 
}) => {
  const { data: customers, isLoading, isError } = useCustomers();
  
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onSelectCustomer(e.target.value);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Select Customer</CardTitle>
      </CardHeader>
      
      <CardContent>
        {isLoading && <div>Loading customers...</div>}
        {isError && (
          <Alert variant="danger">
            Error loading customers. Please try again.
          </Alert>
        )}
        
        {customers && customers.length > 0 && (
          <FormGroup>
            <Label>Customer</Label>
            <Select value={selectedCustomerId} onChange={handleChange}>
              <option value="">Select a customer</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} ({customer.company_name})
                </option>
              ))}
            </Select>
          </FormGroup>
        )}
      </CardContent>
    </Card>
  );
};

export default CustomerSelect; 