# Fubble Web Demo

A web-based demonstration of the Fubble usage-based billing system. This project showcases how to integrate with the Fubble API to implement usage tracking, invoice generation, and billing visualization.

## Features

- Customer management and selection
- Real-time usage event recording
- Usage summary visualization
- Invoice generation
- Invoice viewing and display

## Tech Stack

- React 19
- TypeScript
- Vite
- React Router for navigation
- TanStack Query (formerly React Query) for data fetching
- Styled Components for styling

## Getting Started

### Prerequisites

- Node.js (v18+)
- npm or yarn
- Running Fubble backend server (default: http://localhost:8000)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open your browser to http://localhost:5173

## Usage Flow

1. Select a customer from the dropdown
2. Record usage events for the selected customer
3. View the usage summary showing accumulated metrics
4. Generate invoices for a specific time period
5. View detailed invoices with line items

## Demo Environment

The web demo is pre-configured to work with a demo environment that includes:

- Sample customers (consumers and API providers)
- Predefined pricing plans (Basic and Premium)
- Subscriptions connecting customers to plans

To modify the demo environment, edit the configuration files or use the API directly. It's best to use
the `demo.py` script in the `fubble` app directory.