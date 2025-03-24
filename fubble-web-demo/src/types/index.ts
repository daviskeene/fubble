// Types for Fubble Web Demo

// Customer type
export interface Customer {
  id?: string;
  name: string;
  email: string;
  company_name: string;
  billing_address: string;
  payment_method_id: string;
}

// Price Component types
export type PricingType = 
  | 'flat'
  | 'tiered'
  | 'volume'
  | 'package'
  | 'graduated'
  | 'threshold'
  | 'subscription'
  | 'usage_based_subscription'
  | 'dynamic'
  | 'time_based'
  | 'dimension_based';

export interface PriceTier {
  start: number;
  end: number | null;
  price: number;
}

export interface PriceComponent {
  metric_name: string;
  display_name: string;
  pricing_type: PricingType;
  pricing_details: {
    tiers?: PriceTier[];
    amount?: number;
    rate_per_unit?: number;
    unit?: string;
  };
}

// Pricing Plan type
export type BillingFrequency = 'monthly' | 'quarterly' | 'yearly';

export interface Plan {
  id?: string;
  name: string;
  description: string;
  billing_frequency: BillingFrequency;
  price_components: PriceComponent[];
}

// Subscription type
export interface Subscription {
  id?: string;
  plan_id: string;
  start_date: string;
  end_date: string | null;
}

// Usage Event type
export interface UsageEvent {
  id?: string;
  customer_id: string;
  metric_name: string;
  quantity: number;
  event_time?: string;
  properties?: Record<string, any>;
}

// Invoice types
export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'failed' | 'void';

export interface InvoiceItem {
  id?: string;
  description: string;
  quantity?: number;
  unit_price: number;
  amount: number;
}

export interface Invoice {
  id?: string;
  invoice_number: string;
  customer_id: string;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  amount: number;
  notes?: string;
  invoice_items: InvoiceItem[];
}

// Usage Summary type
export interface UsageSummary {
  [metric: string]: number;
} 