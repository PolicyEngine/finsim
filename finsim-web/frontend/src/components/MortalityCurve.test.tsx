import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MortalityCurve from './MortalityCurve'

describe('MortalityCurve', () => {
  const defaultProps = {
    currentAge: 65,
    gender: 'Male' as const,
    maxAge: 95
  }

  it('should render without crashing', () => {
    render(<MortalityCurve {...defaultProps} />)
    expect(screen.getByText('Survival probability')).toBeInTheDocument()
  })

  it('should display life expectancy', () => {
    render(<MortalityCurve {...defaultProps} />)
    
    expect(screen.getByText(/Your life expectancy:/)).toBeInTheDocument()
    expect(screen.getByText(/\d+ years/)).toBeInTheDocument()
  })

  it('should display 50% survival age', () => {
    render(<MortalityCurve {...defaultProps} />)
    
    expect(screen.getByText(/50% survival age:/)).toBeInTheDocument()
    expect(screen.getByText(/\d+ years/)).toBeInTheDocument()
  })

  it('should show different life expectancy for different genders', () => {
    const { rerender } = render(<MortalityCurve {...defaultProps} gender="Male" />)
    const maleText = screen.getByText(/Your life expectancy:/).parentElement?.textContent
    
    rerender(<MortalityCurve {...defaultProps} gender="Female" />)
    const femaleText = screen.getByText(/Your life expectancy:/).parentElement?.textContent
    
    // Female life expectancy should generally be higher
    expect(maleText).not.toBe(femaleText)
  })

  it('should show spouse information when enabled', () => {
    render(
      <MortalityCurve 
        {...defaultProps} 
        showSpouse={true}
        spouseAge={62}
        spouseGender="Female"
      />
    )
    
    expect(screen.getByText(/Spouse life expectancy:/)).toBeInTheDocument()
    
    // Legend should show both lines
    expect(screen.getByText(/You \(Male, age 65\)/)).toBeInTheDocument()
    expect(screen.getByText(/Spouse \(Female, age 62\)/)).toBeInTheDocument()
  })

  it('should show joint survival curves for couples', () => {
    render(
      <MortalityCurve 
        {...defaultProps} 
        showSpouse={true}
        spouseAge={62}
        spouseGender="Female"
      />
    )
    
    expect(screen.getByText('Both alive')).toBeInTheDocument()
    expect(screen.getByText('Either alive')).toBeInTheDocument()
  })

  it('should show explanation text for single person', () => {
    render(<MortalityCurve {...defaultProps} />)
    
    expect(screen.getByText(/Understanding the chart:/)).toBeInTheDocument()
    expect(screen.getByText(/SSA mortality tables/)).toBeInTheDocument()
    expect(screen.getByText(/individual outcomes vary/)).toBeInTheDocument()
  })

  it('should show explanation text for couples', () => {
    render(
      <MortalityCurve 
        {...defaultProps} 
        showSpouse={true}
        spouseAge={62}
        spouseGender="Female"
      />
    )
    
    expect(screen.getByText(/joint curves show probabilities for couples/)).toBeInTheDocument()
    expect(screen.getByText(/both alive.*both partners/)).toBeInTheDocument()
    expect(screen.getByText(/either alive.*at least one/)).toBeInTheDocument()
  })

  it('should handle very young ages', () => {
    render(<MortalityCurve {...defaultProps} currentAge={25} />)
    
    expect(screen.getByText('Survival probability')).toBeInTheDocument()
    expect(screen.getByText(/Your life expectancy:/)).toBeInTheDocument()
  })

  it('should handle very old ages', () => {
    render(<MortalityCurve {...defaultProps} currentAge={90} maxAge={100} />)
    
    expect(screen.getByText('Survival probability')).toBeInTheDocument()
    expect(screen.getByText(/Your life expectancy:/)).toBeInTheDocument()
  })

  it('should update when age changes', () => {
    const { rerender } = render(<MortalityCurve {...defaultProps} currentAge={65} />)
    const age65Text = screen.getByText(/Your life expectancy:/).parentElement?.textContent
    
    rerender(<MortalityCurve {...defaultProps} currentAge={75} />)
    const age75Text = screen.getByText(/Your life expectancy:/).parentElement?.textContent
    
    // Life expectancy should be different
    expect(age65Text).not.toBe(age75Text)
  })

  it('should use correct colors from theme', () => {
    const { container } = render(<MortalityCurve {...defaultProps} />)
    
    // Check that the component uses the pe-card class
    expect(container.querySelector('.pe-card')).toBeInTheDocument()
  })
})