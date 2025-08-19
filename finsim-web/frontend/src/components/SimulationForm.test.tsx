import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SimulationForm from './SimulationForm'

describe('SimulationForm', () => {
  const defaultProps = {
    onSubmit: vi.fn()
  }

  it('should render all form fields', () => {
    render(<SimulationForm {...defaultProps} />)
    
    expect(screen.getByLabelText(/Current Age/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Gender/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Social Security/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/State/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Expected Return/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Return Volatility/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Annual Spending/i)).toBeInTheDocument()
  })

  it('should have default values', () => {
    render(<SimulationForm {...defaultProps} />)
    
    expect(screen.getByLabelText(/Current Age/i)).toHaveValue(65)
    expect(screen.getByLabelText(/Social Security/i)).toHaveValue(24000)
    expect(screen.getByLabelText(/Expected Return/i)).toHaveValue(7)
    expect(screen.getByLabelText(/Return Volatility/i)).toHaveValue(18)
  })

  it('should update values when user types', () => {
    render(<SimulationForm {...defaultProps} />)
    
    const ageInput = screen.getByLabelText(/Current Age/i)
    fireEvent.change(ageInput, { target: { value: '70' } })
    
    expect(ageInput).toHaveValue(70)
  })

  it('should call onSubmit with form data', async () => {
    const onSubmit = vi.fn()
    render(<SimulationForm onSubmit={onSubmit} />)
    
    const spendingInput = screen.getByLabelText(/Annual Spending/i)
    fireEvent.change(spendingInput, { target: { value: '50000' } })
    
    const submitButton = screen.getByRole('button', { name: /Run Simulation/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
        current_age: 65,
        gender: 'Male',
        social_security: 24000,
        state: 'CA',
        expected_return: 7,
        return_volatility: 18,
        spending_level: 50000
      }))
    })
  })

  it('should validate required fields', async () => {
    render(<SimulationForm {...defaultProps} />)
    
    const spendingInput = screen.getByLabelText(/Annual Spending/i)
    fireEvent.change(spendingInput, { target: { value: '' } })
    
    const submitButton = screen.getByRole('button', { name: /Run Simulation/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Spending level is required/i)).toBeInTheDocument()
    })
    
    expect(defaultProps.onSubmit).not.toHaveBeenCalled()
  })

  it('should disable submit button while submitting', () => {
    render(<SimulationForm {...defaultProps} isSubmitting={true} />)
    
    const submitButton = screen.getByRole('button', { name: /Running.../i })
    expect(submitButton).toBeDisabled()
  })
})