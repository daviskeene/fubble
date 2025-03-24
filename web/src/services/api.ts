import { 
  Customer, 
  Plan, 
  Subscription, 
  UsageEvent, 
  Invoice, 
  UsageSummary 
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

// Helper function to handle fetch responses
const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
  return response.json() as Promise<T>;
};

// Customer API
export const createCustomer = async (customer: Customer): Promise<Customer> => {
  const response = await fetch(`${API_BASE_URL}/customers/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(customer),
  });
  return handleResponse<Customer>(response);
};

export const getCustomers = async (): Promise<Customer[]> => {
  const response = await fetch(`${API_BASE_URL}/customers/`);
  return handleResponse<Customer[]>(response);
};

export const getCustomer = async (id: string): Promise<Customer> => {
  const response = await fetch(`${API_BASE_URL}/customers/${id}`);
  return handleResponse<Customer>(response);
};

// Plan API
export const createPlan = async (plan: Plan): Promise<Plan> => {
  const response = await fetch(`${API_BASE_URL}/plans/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(plan),
  });
  return handleResponse<Plan>(response);
};

export const getPlans = async (activeOnly: boolean = true): Promise<any[]> => {
  const url = `${API_BASE_URL}/plans?active_only=${activeOnly}`;
  const response = await fetch(url);
  return handleResponse<any[]>(response);
};

export const getPlan = async (planId: string): Promise<any> => {
  const url = `${API_BASE_URL}/plans/${planId}`;
  const response = await fetch(url);
  return handleResponse<any>(response);
};

export const getCustomerPlan = async (customerId: string): Promise<any> => {
  try {
    // First, get the customer's active subscription
    const subscriptionsUrl = `${API_BASE_URL}/customers/${customerId}/subscriptions`;
    const subscriptionsResponse = await fetch(subscriptionsUrl);
    
    if (!subscriptionsResponse.ok) {
      console.error('Failed to fetch customer subscriptions:', await subscriptionsResponse.text());
      return null;
    }
    
    const subscriptions = await subscriptionsResponse.json() as Subscription[];
    
    // Find the active subscription (if any)
    const activeSubscription = subscriptions.find(sub => sub.is_active);
    
    if (!activeSubscription) {
      console.info(`No active subscription found for customer ${customerId}`);
      return null;
    }
    
    // Then fetch the full plan details
    const planUrl = `${API_BASE_URL}/plans/${activeSubscription.plan_id}`;
    const planResponse = await fetch(planUrl);
    
    if (!planResponse.ok) {
      console.error('Failed to fetch plan details:', await planResponse.text());
      return null;
    }
    
    const plan = await planResponse.json() as Plan;
    
    // Return subscription and plan information
    return {
      subscription_id: activeSubscription.id,
      subscription: activeSubscription,
      plan: plan
    };
  } catch (error) {
    console.error('Error fetching customer plan:', error);
    return null;
  }
};

// Subscription API
export const createSubscription = async (customerId: string, subscription: Subscription): Promise<Subscription> => {
  const response = await fetch(`${API_BASE_URL}/customers/${customerId}/subscriptions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(subscription),
  });
  return handleResponse<Subscription>(response);
};

export const getSubscriptions = async (customerId: string): Promise<Subscription[]> => {
  const response = await fetch(`${API_BASE_URL}/customers/${customerId}/subscriptions`);
  return handleResponse<Subscription[]>(response);
};

// Events API
export const recordEvent = async (event: UsageEvent): Promise<UsageEvent> => {
  const response = await fetch(`${API_BASE_URL}/events/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(event),
  });
  return handleResponse<UsageEvent>(response);
};

export const getUsageSummary = async (
  customerId: string, 
  startDate: string, 
  endDate: string
): Promise<UsageSummary> => {
  // Ensure the dates are properly encoded
  const encodedStartDate = encodeURIComponent(startDate);
  const encodedEndDate = encodeURIComponent(endDate);
  
  const url = `${API_BASE_URL}/events/customers/${customerId}/usage?start_date=${encodedStartDate}&end_date=${encodedEndDate}`;
  console.log("Fetching usage summary with URL:", url);
  
  const response = await fetch(url);
  return handleResponse<UsageSummary>(response);
};

// Invoice API
export const generateInvoices = async (startDate: string, endDate: string, customerId: string): Promise<Invoice[]> => {
  const encodedStartDate = encodeURIComponent(startDate);
  const encodedEndDate = encodeURIComponent(endDate);
  
  const url = `${API_BASE_URL}/invoices/generate?start_date=${encodedStartDate}&end_date=${encodedEndDate}&customer_id=${customerId}`;
  console.log("Generating invoices with URL:", url);
  
  const response = await fetch(url, {
    method: 'POST',
  });
  return handleResponse<Invoice[]>(response);
};

export const getInvoices = async (): Promise<Invoice[]> => {
  const response = await fetch(`${API_BASE_URL}/invoices/`);
  return handleResponse<Invoice[]>(response);
};

export const getCustomerInvoices = async (customerId: string): Promise<Invoice[]> => {
  const response = await fetch(`${API_BASE_URL}/invoices/customer/${customerId}`);
  return handleResponse<Invoice[]>(response);
};

export const getInvoice = async (id: string): Promise<Invoice> => {
  const response = await fetch(`${API_BASE_URL}/invoices/${id}`);
  return handleResponse<Invoice>(response);
}; 