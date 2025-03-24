import styled from 'styled-components';

// Layout components
export const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  width: 100%;
  
  @media (min-width: 768px) {
    padding: 2rem;
  }
`;

export const FlexContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  width: 100%;
  justify-content: center;
  margin-bottom: 2rem;
`;

export const FlexColumn = styled.div<{ width?: string }>`
  flex: ${props => props.width || '1'};
  min-width: 300px;
  width: 100%;
  
  @media (max-width: 768px) {
    min-width: 100%;
  }
`;

// Card components
export const Card = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  width: 100%;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.1);
  }

  overflow: scroll;
  text-overflow: ellipsis;
`;

export const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
`;

export const CardTitle = styled.h2`
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
`;

export const CardContent = styled.div`
  margin-bottom: 1.25rem;
`;

export const CardFooter = styled.div`
  display: flex;
  justify-content: flex-end;
  padding-top: 0.75rem;
  border-top: 1px solid #f0f0f0;
`;

// Form components
export const FormGroup = styled.div`
  margin-bottom: 1.25rem;
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #555;
`;

export const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  
  &:focus {
    border-color: #3b82f6;
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

export const Select = styled.select`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  transition: border-color 0.2s, box-shadow 0.2s;
  
  &:focus {
    border-color: #3b82f6;
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

export const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  min-height: 120px;
  transition: border-color 0.2s, box-shadow 0.2s;
  resize: vertical;
  
  &:focus {
    border-color: #3b82f6;
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

// Button components
export const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background-color: ${props => {
    switch (props.variant) {
      case 'secondary':
        return '#64748b';
      case 'danger':
        return '#ef4444';
      default:
        return '#3b82f6';
    }
  }};
  color: white;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    background-color: ${props => {
      switch (props.variant) {
        case 'secondary':
          return '#475569';
        case 'danger':
          return '#dc2626';
        default:
          return '#2563eb';
      }
    }};
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

// Table components
export const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
`;

export const TableHead = styled.thead`
  background-color: #f8fafc;
`;

export const TableRow = styled.tr`
  &:nth-child(even) {
    background-color: #f8fafc;
  }
  
  &:hover {
    background-color: #f1f5f9;
  }
`;

export const TableHeader = styled.th`
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
`;

export const TableCell = styled.td`
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
`;

// Alert components
export const Alert = styled.div<{ variant?: 'success' | 'warning' | 'danger' | 'info' }>`
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  background-color: ${props => {
    switch (props.variant) {
      case 'success':
        return '#f0fdf4';
      case 'warning':
        return '#fffbeb';
      case 'danger':
        return '#fef2f2';
      case 'info':
      default:
        return '#f0f9ff';
    }
  }};
  
  color: ${props => {
    switch (props.variant) {
      case 'success':
        return '#16a34a';
      case 'warning':
        return '#d97706';
      case 'danger':
        return '#dc2626';
      case 'info':
      default:
        return '#0284c7';
    }
  }};
  
  border-left: 4px solid ${props => {
    switch (props.variant) {
      case 'success':
        return '#16a34a';
      case 'warning':
        return '#d97706';
      case 'danger':
        return '#dc2626';
      case 'info':
      default:
        return '#0284c7';
    }
  }};
`;

// Invoice specific components
export const InvoiceContainer = styled.div`
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
`;

export const InvoiceHeader = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
`;

export const InvoiceTitle = styled.h1`
  font-size: 2rem;
  color: #333;
  margin: 0;
`;

export const InvoiceInfo = styled.div`
  margin-bottom: 20px;
`;

export const InvoiceRow = styled.div`
  display: flex;
  margin-bottom: 5px;
`;

export const InvoiceLabel = styled.div`
  font-weight: 600;
  width: 150px;
`;

export const InvoiceValue = styled.div`
  flex: 1;
`;

export const InvoiceTotal = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 1.2rem;
  font-weight: 700;
  margin-top: 20px;
  padding-top: 10px;
  border-top: 2px solid #333;
`;

// Dashboard specific components
export const DashboardHeader = styled.header`
  margin-bottom: 2rem;
  padding: 1.5rem;
  background-color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  
  @media (min-width: 768px) {
    flex-direction: row;
    justify-content: space-between;
    padding: 1.5rem 2rem;
  }
`;

export const DashboardTitle = styled.h1`
  font-size: 1.75rem;
  color: #1e293b;
  margin: 0;
  font-weight: 600;
  
  @media (min-width: 768px) {
    font-size: 2rem;
  }
`;

export const PageSection = styled.section`
  margin-bottom: 2rem;
`;

export const SectionTitle = styled.h2`
  font-size: 1.5rem;
  color: #334155;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-align: center;
`;

export const DashboardNav = styled.div`
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin: 1rem 0;
`;

export const NavLink = styled.a`
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  color: var(--color-primary);
  background-color: white;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    color: var(--color-primary-hover);
  }
`;

export const MetricCard = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
`;

export const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #0d6efd;
  margin: 10px 0;
`;

export const MetricLabel = styled.div`
  color: #6c757d;
  font-size: 0.9rem;
`; 