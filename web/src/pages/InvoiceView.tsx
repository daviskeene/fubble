import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import InvoiceDetail from '../components/InvoiceDetail';
import { 
  Container, 
  DashboardHeader, 
  DashboardTitle,
  Button,
  Card,
  PageSection
} from '../components/styled';

const InvoiceView: React.FC = () => {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const navigate = useNavigate();
  
  const handleBackToDashboard = () => {
    navigate('/');
  };
  
  if (!invoiceId) {
    return (
      <Container>
        <Card>Invoice ID not found</Card>
      </Container>
    );
  }
  
  return (
    <>
      <DashboardHeader>
        <DashboardTitle>Invoice Details</DashboardTitle>
        <Button onClick={handleBackToDashboard} variant="secondary">
          Back to Dashboard
        </Button>
      </DashboardHeader>
      
      <Container>
        <PageSection>
          <InvoiceDetail invoiceId={invoiceId} />
        </PageSection>
      </Container>
    </>
  );
};

export default InvoiceView; 