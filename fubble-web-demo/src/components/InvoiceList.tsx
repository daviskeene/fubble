import React from 'react';
import { useInvoices, useCustomerInvoices } from '../hooks/useInvoices';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableCell,
  Button,
  Alert
} from './styled';

interface InvoiceListProps {
  customerId?: string;
  onSelectInvoice: (invoiceId: string) => void;
}

const InvoiceList: React.FC<InvoiceListProps> = ({ customerId, onSelectInvoice }) => {
  // Use either all invoices or customer-specific invoices based on whether customerId is provided
  const { 
    data: customerInvoices, 
    isLoading: isLoadingCustomer, 
    isError: isErrorCustomer 
  } = useCustomerInvoices(customerId || '');
  
  const invoices = customerId && customerInvoices;
  const isLoading = customerId && isLoadingCustomer;
  const isError = customerId && isErrorCustomer;
  
  const handleInvoiceClick = (invoiceId: string) => {
    onSelectInvoice(invoiceId);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {customerId ? 'Customer Invoices' : 'All Invoices'}
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        {isLoading && <div>Loading invoices...</div>}
        {isError && (
          <Alert variant="danger">
            Error loading invoices. Please try again.
          </Alert>
        )}
        
        {invoices && invoices.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Invoice #</TableHeader>
                <TableHeader>Date</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Amount</TableHeader>
                <TableHeader>Action</TableHeader>
              </TableRow>
            </TableHead>
            <tbody>
              {invoices.map(invoice => (
                <TableRow key={invoice.id}>
                  <TableCell>{invoice.invoice_number}</TableCell>
                  <TableCell>{new Date(invoice.issue_date).toLocaleDateString()}</TableCell>
                  <TableCell>{invoice.status.toUpperCase()}</TableCell>
                  <TableCell>${invoice.amount.toFixed(2)}</TableCell>
                  <TableCell>
                    <Button onClick={() => handleInvoiceClick(invoice.id!)}>
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </tbody>
          </Table>
        ) : (
          <div>No invoices available</div>
        )}
      </CardContent>
    </Card>
  );
};

export default InvoiceList; 