import React from 'react';
import { useInvoice } from '../hooks/useInvoices';
import { useCustomer } from '../hooks/useCustomers';
import { 
  InvoiceContainer, 
  InvoiceHeader, 
  InvoiceTitle, 
  InvoiceInfo, 
  InvoiceRow, 
  InvoiceLabel, 
  InvoiceValue,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableCell,
  InvoiceTotal
} from './styled';

interface InvoiceDetailProps {
  invoiceId: string;
}

const InvoiceDetail: React.FC<InvoiceDetailProps> = ({ invoiceId }) => {
  const { data: invoice, isLoading: isLoadingInvoice } = useInvoice(invoiceId);
  const { data: customer, isLoading: isLoadingCustomer } = useCustomer(
    invoice?.customer_id || ''
  );
  
  if (isLoadingInvoice || isLoadingCustomer) {
    return <div>Loading invoice details...</div>;
  }
  
  if (!invoice) {
    return <div>Invoice not found</div>;
  }
  
  return (
    <InvoiceContainer>
      <InvoiceHeader>
        <InvoiceTitle>Invoice</InvoiceTitle>
        <div>
          <div><strong>Invoice #{invoice.invoice_number}</strong></div>
          <div>{invoice.status.toUpperCase()}</div>
        </div>
      </InvoiceHeader>
      
      <InvoiceInfo>
        <InvoiceRow>
          <InvoiceLabel>Customer:</InvoiceLabel>
          <InvoiceValue>{customer?.name}</InvoiceValue>
        </InvoiceRow>
        <InvoiceRow>
          <InvoiceLabel>Company:</InvoiceLabel>
          <InvoiceValue>{customer?.company_name}</InvoiceValue>
        </InvoiceRow>
        <InvoiceRow>
          <InvoiceLabel>Billing Address:</InvoiceLabel>
          <InvoiceValue>{customer?.billing_address}</InvoiceValue>
        </InvoiceRow>
      </InvoiceInfo>
      
      <InvoiceInfo>
        <InvoiceRow>
          <InvoiceLabel>Issue Date:</InvoiceLabel>
          <InvoiceValue>{new Date(invoice.issue_date).toLocaleDateString()}</InvoiceValue>
        </InvoiceRow>
        <InvoiceRow>
          <InvoiceLabel>Due Date:</InvoiceLabel>
          <InvoiceValue>{new Date(invoice.due_date).toLocaleDateString()}</InvoiceValue>
        </InvoiceRow>
      </InvoiceInfo>
      
      <Table>
        <TableHead>
          <TableRow>
            <TableHeader>Description</TableHeader>
            <TableHeader>Amount</TableHeader>
          </TableRow>
        </TableHead>
        <tbody>
          {invoice.invoice_items.map((item, index) => (
            <TableRow key={index}>
              <TableCell>{item.description}</TableCell>
              <TableCell>${item.amount.toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </tbody>
      </Table>
      
      <InvoiceTotal>
        <div>Total</div>
        <div>${invoice.amount.toFixed(2)}</div>
      </InvoiceTotal>
      
      {invoice.notes && (
        <InvoiceInfo>
          <InvoiceRow>
            <InvoiceLabel>Notes:</InvoiceLabel>
            <InvoiceValue>{invoice.notes}</InvoiceValue>
          </InvoiceRow>
        </InvoiceInfo>
      )}
    </InvoiceContainer>
  );
};

export default InvoiceDetail; 