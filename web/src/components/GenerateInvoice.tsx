import React, { useState } from 'react';
import { useGenerateInvoices } from '../hooks/useInvoices';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent, 
  CardFooter, 
  FormGroup, 
  Label, 
  Input, 
  Button,
  Alert
} from './styled';

interface GenerateInvoiceProps {
  onInvoicesGenerated?: () => void;
}

const GenerateInvoice: React.FC<GenerateInvoiceProps> = ({ onInvoicesGenerated }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  
  const { mutate: generateInvoices, isPending, isError, error } = useGenerateInvoices();
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Format dates to ISO string - make sure to set time to start/end of day
    const startDateTime = new Date(startDate);
    startDateTime.setHours(0, 0, 0, 0); // Start of day
    
    const endDateTime = new Date(endDate);
    endDateTime.setHours(23, 59, 59, 999); // End of day
    
    // Create ISO strings but remove the 'Z' suffix as needed by the API
    const startISODate = startDateTime.toISOString().replace('Z', '');
    const endISODate = endDateTime.toISOString().replace('Z', '');
    
    console.log("Invoice generation start date:", startISODate);
    console.log("Invoice generation end date:", endISODate);
    
    generateInvoices(
      { startDate: startISODate, endDate: endISODate },
      {
        onSuccess: () => {
          setShowSuccess(true);
          
          // Hide success message after 3 seconds
          setTimeout(() => setShowSuccess(false), 3000);
          
          // Call the callback if provided
          if (onInvoicesGenerated) {
            onInvoicesGenerated();
          }
        }
      }
    );
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Invoices</CardTitle>
      </CardHeader>
      
      <CardContent>
        {showSuccess && (
          <Alert variant="success">
            Invoices generated successfully!
          </Alert>
        )}
        
        {isError && (
          <Alert variant="danger">
            {(error as Error)?.message || 'Failed to generate invoices. Please try again.'}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <FormGroup>
            <Label>Start Date</Label>
            <Input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label>End Date</Label>
            <Input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </FormGroup>
          
          <CardFooter>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Generating...' : 'Generate Invoices'}
            </Button>
          </CardFooter>
        </form>
      </CardContent>
    </Card>
  );
};

export default GenerateInvoice; 