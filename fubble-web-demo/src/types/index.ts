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
  id: number;
  plan_id: number;
  metric_name: string;
  display_name: string;
  pricing_type: string; // 'flat', 'tiered', 'volume', or 'package'
  pricing_details: any;
  created_at: string;
  updated_at: string;
}

// Pricing Plan type
export type BillingFrequency = 'monthly' | 'quarterly' | 'yearly';

export interface Plan {
  id: number;
  name: string;
  description: string;
  billing_frequency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  price_components: PriceComponent[];
}

// Subscription type
export interface Subscription {
  id?: string;
  customer_id: string;
  plan_id: string;
  status: string;
  start_date: string;
  end_date?: string;
  auto_renew: boolean;
  plan?: Plan;
  is_active: boolean;
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