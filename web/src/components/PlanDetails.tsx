import React from 'react';
import { useCustomerPlan } from '../hooks/usePlans';
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
  Alert
} from './styled';
import { PriceComponent } from '../types';

interface PlanDetailsProps {
  customerId: string;
}

const PlanDetails: React.FC<PlanDetailsProps> = ({ customerId }) => {
  const { data, isLoading, isError } = useCustomerPlan(customerId);

  const formatPricingType = (type: string): string => {
    switch (type) {
      case 'flat':
        return 'Flat Fee';
      case 'tiered':
        return 'Tiered Pricing';
      case 'volume':
        return 'Volume Pricing';
      case 'package':
        return 'Package Pricing';
      case 'time_based':
        return 'Time-Based Pricing';
      case 'subscription':
        return 'Subscription Fee';
      case 'graduated':
        return 'Graduated Pricing';
      case 'threshold':
        return 'Threshold Pricing';
      default:
        return type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
    }
  };

  const formatBillingFrequency = (frequency: string): string => {
    switch (frequency) {
      case 'monthly':
        return 'Monthly';
      case 'quarterly':
        return 'Quarterly';
      case 'yearly':
        return 'Yearly';
      default:
        return frequency.charAt(0).toUpperCase() + frequency.slice(1);
    }
  };

  const formatPricingDetails = (component: PriceComponent): string => {
    const { pricing_type, pricing_details } = component;
    
    if (!pricing_details) return 'N/A';
    
    try {
      switch (pricing_type) {
        case 'flat':
        case 'subscription':
          return `$${Number(pricing_details.amount).toFixed(2)}`;
        case 'package':
          return `$${Number(pricing_details.package_price).toFixed(2)} per ${pricing_details.package_size} units`;
        case 'time_based':
          return `$${Number(pricing_details.rate_per_unit).toFixed(6)} per ${pricing_details.unit || 'unit'}`;
        case 'tiered':
        case 'volume':
          if (pricing_details.tiers && pricing_details.tiers.length > 0) {
            const firstTier = pricing_details.tiers[0];
            const price = firstTier.price !== undefined ? firstTier.price : firstTier.unit_price;
            
            return `$${Number(price).toFixed(4)} per unit for first ${firstTier.end || 'unlimited'} units${pricing_details.tiers.length > 1 ? ' + more tiers' : ''}`;
          }
          return 'Custom tiered pricing';
        default:
          return 'Custom pricing';
      }
    } catch (error) {
      console.error('Error formatting pricing details:', error);
      return 'Error displaying pricing';
    }
  };

  // New function to render detailed tier information
  const renderDetailedTiers = (component: PriceComponent) => {
    const { pricing_details } = component;
    
    if (!pricing_details || !pricing_details.tiers || pricing_details.tiers.length <= 1) {
      return null;
    }
    
    return (
      <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#64748b' }}>
        <div>Tier details:</div>
        <ul style={{ margin: '0.25rem 0 0 1rem', paddingLeft: 0 }}>
          {pricing_details.tiers.map((tier: any, index: number) => {
            const start = tier.start;
            const end = tier.end !== null ? tier.end : '∞';
            const price = tier.price !== undefined ? tier.price : tier.unit_price;
            
            try {
              return (
                <li key={index} style={{ marginBottom: '0.125rem' }}>
                  {typeof start === 'number' ? start.toLocaleString() : start} - {typeof end === 'number' ? end.toLocaleString() : end}: ${Number(price).toFixed(4)} per unit
                </li>
              );
            } catch (error) {
              console.error('Error rendering tier:', error);
              return <li key={index}>Error displaying tier information</li>;
            }
          })}
        </ul>
      </div>
    );
  };

  // Special display for subscription fees at the top level
  const renderSubscriptionFee = () => {
    if (!data || !data.plan || !data.plan.price_components) return null;
    
    const subscriptionComponent = data.plan.price_components.find(
      comp => comp.pricing_type === 'subscription'
    );
    
    if (!subscriptionComponent) return null;
    
    return (
      <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#f0f9ff', borderRadius: '8px' }}>
        <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
          {subscriptionComponent.display_name}
        </div>
        <div style={{ fontSize: '1.25rem', color: '#0284c7' }}>
          ${Number(subscriptionComponent.pricing_details.amount).toFixed(2)} / {formatBillingFrequency(data.plan.billing_frequency)}
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Plan</CardTitle>
      </CardHeader>
      
      <CardContent>
        {isLoading && <div>Loading plan information...</div>}
        {isError && (
          <Alert variant="danger">
            Error loading plan information. Please try again.
          </Alert>
        )}
        
        {data && data.plan ? (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ marginBottom: '0.5rem' }}>{data.plan.name}</h3>
              <p style={{ color: '#64748b' }}>
                {data.plan.description}
              </p>
              <p>
                <strong>Billing:</strong> {formatBillingFrequency(data.plan.billing_frequency)}
              </p>
              {data.subscription && (
                <p>
                  <strong>Status:</strong> {data.subscription.status?.toUpperCase() || 
                                           (data.subscription.is_active ? 'ACTIVE' : 'INACTIVE')}
                </p>
              )}
            </div>
            
            {renderSubscriptionFee()}
            
            <h4 style={{ marginBottom: '0.75rem' }}>Pricing Components</h4>
            
            {data.plan.price_components.length > 0 ? (
              <>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeader>Service</TableHeader>
                      <TableHeader>Pricing Type</TableHeader>
                      <TableHeader>Rate</TableHeader>
                    </TableRow>
                  </TableHead>
                  <tbody>
                    {data.plan.price_components
                      // Don't show subscription components in table since they're displayed above
                      .filter(component => component.pricing_type !== 'subscription')
                      .map((component) => (
                        <React.Fragment key={component.id}>
                          <TableRow>
                            <TableCell>{component.display_name}</TableCell>
                            <TableCell>{formatPricingType(component.pricing_type)}</TableCell>
                            <TableCell>{formatPricingDetails(component)}</TableCell>
                          </TableRow>
                          {(component.pricing_type === 'tiered' || component.pricing_type === 'volume') && 
                           component.pricing_details?.tiers?.length > 1 && (
                            <TableRow>
                              <TableCell colSpan={3} style={{ padding: '0 1rem 1rem 2rem', backgroundColor: '#f9fafb' }}>
                                {renderDetailedTiers(component)}
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      ))}
                  </tbody>
                </Table>
              </>
            ) : (
              <p>No pricing components defined for this plan.</p>
            )}
          </>
        ) : !isLoading && (
          <Alert variant="info">
            No active subscription found for this customer.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default PlanDetails; 