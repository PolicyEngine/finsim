import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StockProjection from './StockProjection'

describe('StockProjection', () => {
  const defaultProps = {
    expectedReturn: 7.0,
    volatility: 18.0,
    currentValue: 100,
    years: 30
  }

  it('should render without crashing', () => {
    render(<StockProjection {...defaultProps} />)
    expect(screen.getByText('Projected growth path')).toBeInTheDocument()
  })

  it('should display expected return and volatility', () => {
    render(<StockProjection {...defaultProps} />)
    
    expect(screen.getByText(/Expected return:/)).toBeInTheDocument()
    expect(screen.getByText(/7\.0% annually/)).toBeInTheDocument()
    expect(screen.getByText(/Volatility:/)).toBeInTheDocument()
    expect(screen.getByText(/18\.0%/)).toBeInTheDocument()
  })

  it('should display starting value', () => {
    render(<StockProjection {...defaultProps} />)
    
    expect(screen.getByText(/Starting value:/)).toBeInTheDocument()
    expect(screen.getByText(/\$100/)).toBeInTheDocument()
  })

  it('should format large portfolio values correctly', () => {
    render(<StockProjection {...defaultProps} currentValue={500000} />)
    
    expect(screen.getByText(/\$500,000/)).toBeInTheDocument()
  })

  it('should show explanation text', () => {
    render(<StockProjection {...defaultProps} />)
    
    expect(screen.getByText(/Understanding the chart:/)).toBeInTheDocument()
    expect(screen.getByText(/confidence intervals/)).toBeInTheDocument()
    expect(screen.getByText(/historical volatility/)).toBeInTheDocument()
  })

  it('should calculate projections for different time horizons', () => {
    const { rerender } = render(<StockProjection {...defaultProps} years={10} />)
    
    // Chart should be rendered (ResponsiveContainer renders a div)
    expect(screen.getByText('Projected growth path')).toBeInTheDocument()
    
    // Change to 20 years
    rerender(<StockProjection {...defaultProps} years={20} />)
    expect(screen.getByText('Projected growth path')).toBeInTheDocument()
  })

  it('should handle zero volatility', () => {
    render(<StockProjection {...defaultProps} volatility={0} />)
    
    expect(screen.getByText(/0\.0%/)).toBeInTheDocument()
    expect(screen.getByText('Projected growth path')).toBeInTheDocument()
  })

  it('should handle negative returns', () => {
    render(<StockProjection {...defaultProps} expectedReturn={-5.0} />)
    
    expect(screen.getByText(/-5\.0% annually/)).toBeInTheDocument()
  })

  it('should use correct colors from theme', () => {
    const { container } = render(<StockProjection {...defaultProps} />)
    
    // Check that the component uses the pe-card class
    expect(container.querySelector('.pe-card')).toBeInTheDocument()
  })

  it('should show confidence interval explanation', () => {
    render(<StockProjection {...defaultProps} />)
    
    expect(screen.getByText(/50% confidence/)).toBeInTheDocument()
    expect(screen.getByText(/90% confidence/)).toBeInTheDocument()
    expect(screen.getByText(/wider spread over time/)).toBeInTheDocument()
  })
})