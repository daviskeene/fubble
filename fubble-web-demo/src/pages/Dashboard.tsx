import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import CustomerSelect from '../components/CustomerSelect';
import EventForm from '../components/EventForm';
import UsageSummary from '../components/UsageSummary';
import GenerateInvoice from '../components/GenerateInvoice';
import InvoiceList from '../components/InvoiceList';
import { 
  Container, 
  DashboardHeader, 
  DashboardTitle,
  FlexContainer,
  FlexColumn,
  PageSection,
  SectionTitle
} from '../components/styled';

const Dashboard: React.FC = () => {
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const handleSelectCustomer = useCallback((customerId: string) => {
    setSelectedCustomerId(customerId);
  }, []);
  
  const handleSelectInvoice = useCallback((invoiceId: string) => {
    navigate(`/invoices/${invoiceId}`);
  }, [navigate]);
  
  const handleInvoicesGenerated = useCallback(() => {
    // Invalidate relevant queries to trigger refetching
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ 
      queryKey: ['customerInvoices', selectedCustomerId] 
    });
  }, [queryClient, selectedCustomerId]);
  
  const handleEventRecorded = useCallback(() => {
    // Invalidate usage summary to trigger real-time update
    const now = new Date();
    const oneMonthAgo = new Date(now);
    oneMonthAgo.setMonth(now.getMonth() - 1);
    
    const end = now.toISOString().replace('Z', '');
    const start = oneMonthAgo.toISOString().replace('Z', '');
    
    queryClient.invalidateQueries({ 
      queryKey: ['usageSummary', selectedCustomerId, start, end] 
    });
  }, [queryClient, selectedCustomerId]);
  
  return (
    <>
      <DashboardHeader>
        <DashboardTitle>Fubble Demo Dashboard</DashboardTitle>
      </DashboardHeader>
      
      <Container>
        <PageSection>
          <CustomerSelect
            selectedCustomerId={selectedCustomerId}
            onSelectCustomer={handleSelectCustomer}
          />
        </PageSection>
        
        {selectedCustomerId && (
          <>
            <PageSection>
              <SectionTitle>Usage & Events</SectionTitle>
              <FlexContainer>
                <FlexColumn>
                  <EventForm 
                    customerId={selectedCustomerId} 
                    onEventRecorded={handleEventRecorded}
                  />
                </FlexColumn>
                
                <FlexColumn>
                  <UsageSummary customerId={selectedCustomerId} />
                </FlexColumn>
              </FlexContainer>
            </PageSection>
            
            <PageSection>
              <SectionTitle>Invoices</SectionTitle>
              <FlexContainer>
                <InvoiceList 
                    customerId={selectedCustomerId} 
                    onSelectInvoice={handleSelectInvoice}
                  />
               <FlexColumn>
                  <GenerateInvoice onInvoicesGenerated={handleInvoicesGenerated} />
                </FlexColumn>
              </FlexContainer>
            </PageSection>
          </>
        )}
      </Container>
    </>
  );
};

export default Dashboard; 