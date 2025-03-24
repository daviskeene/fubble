# Fubble Usage Guide

Welcome to Fubble, a flexible usage-based billing system that helps you track, measure, and bill for your customers' service usage. This guide will walk you through how to use Fubble's API to manage your usage-based billing needs.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Getting Started](#getting-started)
3. [Managing Customers](#managing-customers)
4. [Tracking Usage Events](#tracking-usage-events)
5. [Creating Pricing Plans](#creating-pricing-plans)
6. [Managing Subscriptions](#managing-subscriptions)
7. [Generating and Managing Invoices](#generating-and-managing-invoices)
8. [Analyzing Usage Data](#analyzing-usage-data)
9. [API Reference](#api-reference)

## Core Concepts

Fubble is built around these key concepts:

- **Customers**: Organizations or individuals who use your services and are billed based on usage.
- **Plans**: Pricing models that define how different types of usage are billed.
- **Price Components**: Individual billable items within a plan, each with its own pricing type.
- **Usage Events**: Records of service consumption that are tracked and used for billing calculations.
- **Billing Periods**: Timeframes for calculating charges (monthly, quarterly, or yearly).
- **Subscriptions**: Connects customers with plans for a specific time period.
- **Invoices**: Itemized bills generated for customers based on their usage and subscriptions.

## Getting Started

To use Fubble, you'll need to:

1. Create customers in the system
2. Define pricing plans with appropriate pricing components
3. Set up subscriptions linking customers to plans
4. Track usage events as they occur
5. Generate invoices for billing periods

All operations are performed via RESTful API endpoints.

## Managing Customers

### Creating a Customer

```
POST /customers/
```

Request body:
```json
{
  "name": "Acme Corp",
  "email": "billing@acmecorp.com",
  "phone": "+1-555-123-4567",
  "address": "123 Main St, San Francisco, CA 94105",
  "metadata": {
    "industry": "technology",
    "size": "enterprise"
  }
}
```

### Retrieving Customer Information

```
GET /customers/{customer_id}
```

### Updating Customer Details

```
PUT /customers/{customer_id}
```

## Tracking Usage Events

Usage events are the foundation of usage-based billing. Each time a customer uses your service, you should track that as an event.

### Recording a Usage Event

```
POST /events/
```

Request body:
```json
{
  "customer_id": 123,
  "metric_name": "api_calls",
  "quantity": 1.0,
  "event_time": "2023-09-01T12:34:56",
  "properties": {
    "endpoint": "/users",
    "method": "GET",
    "response_time_ms": 45
  }
}
```

The `metric_name` must correspond to a metric that is defined in your pricing plan.

### Retrieving Customer Usage Events

```
GET /events/customers/{customer_id}?start_date=2023-09-01T00:00:00&end_date=2023-09-30T23:59:59
```

You can optionally filter by metric:

```
GET /events/customers/{customer_id}?start_date=2023-09-01T00:00:00&end_date=2023-09-30T23:59:59&metric_name=api_calls
```

### Getting Aggregated Usage

To get the total usage for each metric:

```
GET /events/customers/{customer_id}/usage?start_date=2023-09-01T00:00:00&end_date=2023-09-30T23:59:59
```

## Creating Pricing Plans

Plans define how you bill for different types of usage.

### Creating a Plan

```
POST /plans/
```

Request body:
```json
{
  "name": "API Pro Plan",
  "description": "Professional tier API access with usage-based billing",
  "billing_frequency": "monthly",
  "price_components": [
    {
      "metric_name": "api_calls",
      "display_name": "API Calls",
      "pricing_type": "tiered",
      "pricing_details": {
        "tiers": [
          {"start": 0, "end": 1000, "price": 0.01},
          {"start": 1000, "end": 10000, "price": 0.005},
          {"start": 10000, "end": null, "price": 0.002}
        ]
      }
    },
    {
      "metric_name": "storage_gb",
      "display_name": "Storage",
      "pricing_type": "volume",
      "pricing_details": {
        "tiers": [
          {"start": 0, "end": 100, "price": 0.10},
          {"start": 100, "end": 1000, "price": 0.08},
          {"start": 1000, "end": null, "price": 0.05}
        ]
      }
    },
    {
      "metric_name": "subscription_fee",
      "display_name": "Base Subscription",
      "pricing_type": "subscription",
      "pricing_details": {
        "amount": 29.99
      }
    }
  ]
}
```

### Supported Pricing Types

Fubble supports multiple pricing models to fit your business needs:

1. **Flat**: Simple flat fee regardless of usage
   ```json
   {
     "pricing_type": "flat",
     "pricing_details": {
       "amount": 19.99
     }
   }
   ```

2. **Tiered**: Different rates applied to usage in different tiers
   ```json
   {
     "pricing_type": "tiered",
     "pricing_details": {
       "tiers": [
         {"start": 0, "end": 1000, "price": 0.01},
         {"start": 1000, "end": 10000, "price": 0.005},
         {"start": 10000, "end": null, "price": 0.002}
       ]
     }
   }
   ```

3. **Volume**: Single rate based on total volume
   ```json
   {
     "pricing_type": "volume",
     "pricing_details": {
       "tiers": [
         {"start": 0, "end": 100, "price": 0.10},
         {"start": 100, "end": 1000, "price": 0.08},
         {"start": 1000, "end": null, "price": 0.05}
       ]
     }
   }
   ```

4. **Package**: Units sold in predefined packages
   ```json
   {
     "pricing_type": "package",
     "pricing_details": {
       "package_size": 1000,
       "package_price": 9.99
     }
   }
   ```

5. **Subscription**: Recurring flat fee
   ```json
   {
     "pricing_type": "subscription",
     "pricing_details": {
       "amount": 29.99
     }
   }
   ```

6. **Usage-Based Subscription**: Base fee plus usage charges
   ```json
   {
     "pricing_type": "usage_based_subscription",
     "pricing_details": {
       "base_fee": 20.0,
       "usage_price": 0.5
     }
   }
   ```

7. **Time-Based**: Pricing based on duration
   ```json
   {
     "pricing_type": "time_based",
     "pricing_details": {
       "rate_per_unit": 2.5,
       "unit": "hour"
     }
   }
   ```

8. **Dynamic**: Pricing based on a formula or external factors
   ```json
   {
     "pricing_type": "dynamic",
     "pricing_details": {
       "base_rate": 0.15,
       "formula": "base_rate * (1 + market_factor)"
     }
   }
   ```

## Managing Subscriptions

Subscriptions connect customers to pricing plans.

### Creating a Subscription

```
POST /customers/{customer_id}/subscriptions
```

Request body:
```json
{
  "plan_id": 1,
  "start_date": "2023-09-01T00:00:00",
  "end_date": null
}
```

Setting `end_date` to `null` creates an ongoing subscription.

## Generating and Managing Invoices

### Invoice Lifecycle

Invoices in Fubble follow a specific lifecycle:

1. **Draft**: Initial state, can be modified (add/remove items)
2. **Pending**: Finalized and ready to be sent to customer
3. **Paid**: Payment has been received
4. **Failed**: Payment attempted but failed
5. **Void**: Invoice has been voided/cancelled

Only invoices in the **Draft** state can be modified by adding or removing items.

### Retrieving Invoices

#### Get a Specific Invoice

```
GET /invoices/{invoice_id}
```

#### Get Customer Invoices

```
GET /invoices/customer/{customer_id}
```

Optionally filter by status:

```
GET /invoices/customer/{customer_id}?status=pending
```

#### Get All Invoices by Status

```
GET /invoices?status=pending
```

This endpoint retrieves all invoices with a specific status.

### Manually Creating an Invoice

```
POST /invoices/
```

Request body:
```json
{
  "customer_id": 123,
  "issue_date": "2023-10-01T00:00:00",
  "due_date": "2023-10-15T00:00:00",
  "notes": "Invoice for September 2023 services",
  "items": [
    {
      "description": "API Calls - Tier 1",
      "amount": 10.0,
      "quantity": 1000,
      "metric_name": "api_calls",
      "unit_price": 0.01
    }
  ]
}
```

When creating an invoice:
- If `issue_date` is not provided, it defaults to the current time
- If `due_date` is not provided, it defaults to the issue date plus the default payment term days (usually 30 days)
- The invoice is created with a status of "draft"
- Invoice numbers are automatically generated in the format: `INV-YYYYMMDD-CUSTOMERID-TIMESTAMP`

### Managing Invoice Items

#### Adding an Item to an Invoice

```
POST /invoices/{invoice_id}/items
```

Request body:
```json
{
  "description": "Storage - Tier 2",
  "amount": 24.0,
  "quantity": 300,
  "metric_name": "storage_gb",
  "unit_price": 0.08
}
```

Note:
- Items can only be added to invoices in the "draft" status
- If `unit_price` is not provided but `quantity` is, it will be calculated as `amount / quantity`
- If neither is provided, `unit_price` will equal `amount`
- The invoice total is automatically updated when items are added

#### Removing an Item from an Invoice

```
DELETE /invoices/{invoice_id}/items/{item_id}
```

Items can only be removed from invoices in the "draft" status. The invoice total is automatically updated when items are removed.

### Automatically Generating Invoices

```
POST /invoices/generate
```

Request body:
```json
{
  "start_date": "2023-09-01T00:00:00",
  "end_date": "2023-09-30T23:59:59"
}
```

This endpoint will generate invoices for all customers with active subscriptions during the specified period. The billing engine:

1. Calculates usage for each customer's billing period within the date range
2. Applies the pricing rules from the customer's plan
3. Creates draft invoices with appropriate line items
4. Returns the list of created invoices

### Managing Invoice Status

#### Update an Invoice's Status

```
PUT /invoices/{invoice_id}/status?status=paid
```

Valid status values:
- `draft`: Initial state, can be modified
- `pending`: Finalized and sent to customer
- `paid`: Payment received (automatically sets the paid_date to current time)
- `failed`: Payment failed
- `void`: Invoice voided

#### Finalize an Invoice

```
PUT /invoices/{invoice_id}/finalize
```

Changes an invoice's status from "draft" to "pending". Only invoices in the "draft" status can be finalized.

#### Void an Invoice

```
PUT /invoices/{invoice_id}/void
```

Optional query parameter:
```
reason="Duplicate"
```

Voids an invoice, setting its status to "void". You cannot void an invoice that has already been paid. If a reason is provided, it will be appended to the invoice notes.

## Analyzing Usage Data

Fubble provides endpoints to analyze usage patterns and billing data:

```
GET /events/customers/{customer_id}/usage?start_date=2023-09-01T00:00:00&end_date=2023-09-30T23:59:59
```

Returns aggregated usage by metric for the specified period.

## Best Practices

1. **Regular Event Tracking**: Track usage events as they occur to ensure accurate billing.
2. **Validate Metrics**: Ensure that events use metric names defined in your pricing plans.
3. **Review Invoices**: Always review auto-generated invoices before finalizing them.
4. **Test New Plans**: Test new pricing plans with sample data before assigning them to customers.
5. **Monitor Usage**: Regularly monitor customer usage to identify patterns and potential issues.
6. **Invoice Workflow**: Follow a consistent workflow with invoices:
   - Create invoices in draft status
   - Add all necessary items
   - Review for accuracy
   - Finalize (change to pending)
   - Mark as paid when payment is received

## Troubleshooting

### Common Issues

1. **Missing Billing Periods**: Ensure subscriptions are properly created with the right dates.
2. **Event Not Tracked**: Verify the customer has an active subscription for the given metric.
3. **Incorrect Invoice Amounts**: Check that all usage events were properly recorded during the billing period.
4. **Cannot Modify Invoice**: Only invoices in "draft" status can be modified.
5. **Invoice Number Format**: If you're having trouble finding an invoice, check the format: INV-YYYYMMDD-CUSTOMERID-TIMESTAMP.

For additional support, please contact the Fubble team or refer to the full documentation. 