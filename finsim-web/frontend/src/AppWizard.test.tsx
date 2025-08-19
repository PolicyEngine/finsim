import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import AppWizard from './AppWizard'

// Mock the API module
vi.mock('./services/api', () => ({
  runBatchSimulation: vi.fn(() => Promise.resolve({
    results: {
      stocks_only: {
        success_rate: 0.853,
        median_final_portfolio: 1200000,
        failure_risk_10y: 0.052,
        median_failure_age: 87
      }
    }
  }))
}))

// Mock the components
vi.mock('./components/MarketCalibration', () => ({
  default: ({ onUpdate }: any) => {
    // Trigger update with default values
    React.useEffect(() => {
      onUpdate({
        expected_return: 7.0,
        return_volatility: 18.0,
        dividend_yield: 1.8,
        years_of_data: 10
      })
    }, [onUpdate])
    return <div data-testid="market-calibration">Market Calibration</div>
  }
}))

vi.mock('./components/StockProjection', () => ({
  default: ({ expectedReturn, volatility }: any) => (
    <div data-testid="stock-projection">
      Stock Projection: {expectedReturn}% return, {volatility}% volatility
    </div>
  )
}))

vi.mock('./components/MortalityCurve', () => ({
  default: ({ currentAge, gender }: any) => (
    <div data-testid="mortality-curve">
      Mortality Curve: {gender} age {currentAge}
    </div>
  )
}))

describe('AppWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Step Navigation', () => {
    it('should start on demographics step', () => {
      render(<AppWizard />)
      expect(screen.getByText('Tell us about yourself')).toBeInTheDocument()
      expect(screen.getByText('1. Demographics')).toHaveStyle({ fontWeight: '600' })
    })

    it('should navigate to finances step when clicking next', () => {
      render(<AppWizard />)
      
      const nextButton = screen.getByText('Next: Finances')
      fireEvent.click(nextButton)
      
      expect(screen.getByText('Your financial situation')).toBeInTheDocument()
      expect(screen.getByText('2. Finances')).toHaveStyle({ fontWeight: '600' })
    })

    it('should navigate back to previous step', () => {
      render(<AppWizard />)
      
      // Go to finances
      fireEvent.click(screen.getByText('Next: Finances'))
      expect(screen.getByText('Your financial situation')).toBeInTheDocument()
      
      // Go back to demographics
      fireEvent.click(screen.getByText('Back'))
      expect(screen.getByText('Tell us about yourself')).toBeInTheDocument()
    })

    it('should show all six steps in the indicator', () => {
      render(<AppWizard />)
      
      expect(screen.getByText('1. Demographics')).toBeInTheDocument()
      expect(screen.getByText('2. Finances')).toBeInTheDocument()
      expect(screen.getByText('3. Market')).toBeInTheDocument()
      expect(screen.getByText('4. Review')).toBeInTheDocument()
      expect(screen.getByText('5. Simulate')).toBeInTheDocument()
      expect(screen.getByText('6. Results')).toBeInTheDocument()
    })

    it('should mark completed steps with checkmarks', () => {
      render(<AppWizard />)
      
      // Initially, no checkmarks
      expect(screen.queryByText('✓')).not.toBeInTheDocument()
      
      // Move to finances (demographics is now complete)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      // Should show checkmark for demographics
      const indicators = screen.getAllByText('✓')
      expect(indicators).toHaveLength(1)
    })
  })

  describe('Demographics Step', () => {
    it('should show demographics form fields', () => {
      render(<AppWizard />)
      
      expect(screen.getByLabelText('Current age')).toBeInTheDocument()
      expect(screen.getByLabelText('Gender')).toBeInTheDocument()
      expect(screen.getByLabelText('Retirement age')).toBeInTheDocument()
      expect(screen.getByLabelText('Planning to age')).toBeInTheDocument()
    })

    it('should show spouse fields when checkbox is checked', () => {
      render(<AppWizard />)
      
      const spouseCheckbox = screen.getByLabelText('Include spouse')
      expect(screen.queryByLabelText('Spouse age')).not.toBeInTheDocument()
      
      fireEvent.click(spouseCheckbox)
      
      expect(screen.getByLabelText('Spouse age')).toBeInTheDocument()
      expect(screen.getByLabelText('Spouse gender')).toBeInTheDocument()
    })

    it('should show mortality curve preview', () => {
      render(<AppWizard />)
      expect(screen.getByTestId('mortality-curve')).toBeInTheDocument()
    })

    it('should update mortality curve when age changes', () => {
      render(<AppWizard />)
      
      const ageInput = screen.getByLabelText('Current age')
      fireEvent.change(ageInput, { target: { value: '70' } })
      
      expect(screen.getByText('Mortality Curve: Male age 70')).toBeInTheDocument()
    })

    it('should disable next button with invalid age', () => {
      render(<AppWizard />)
      
      const ageInput = screen.getByLabelText('Current age')
      const nextButton = screen.getByText('Next: Finances')
      
      // Set age to 0 (invalid)
      fireEvent.change(ageInput, { target: { value: '0' } })
      expect(nextButton).toBeDisabled()
      
      // Set valid age
      fireEvent.change(ageInput, { target: { value: '65' } })
      expect(nextButton).not.toBeDisabled()
    })
  })

  describe('Finances Step', () => {
    it('should show financial form fields', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      expect(screen.getByLabelText('Current portfolio value ($)')).toBeInTheDocument()
      expect(screen.getByLabelText('Annual spending need ($)')).toBeInTheDocument()
      expect(screen.getByLabelText('Annual social security ($)')).toBeInTheDocument()
      expect(screen.getByLabelText('Annual pension ($)')).toBeInTheDocument()
      expect(screen.getByLabelText('State (for taxes)')).toBeInTheDocument()
    })

    it('should calculate and display financial summary', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      expect(screen.getByText('Financial summary')).toBeInTheDocument()
      expect(screen.getByText('Spending need')).toBeInTheDocument()
      expect(screen.getByText('Guaranteed income')).toBeInTheDocument()
      expect(screen.getByText('Portfolio need')).toBeInTheDocument()
      expect(screen.getByText('Withdrawal rate')).toBeInTheDocument()
    })

    it('should update withdrawal rate when values change', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      const portfolioInput = screen.getByLabelText('Current portfolio value ($)')
      const spendingInput = screen.getByLabelText('Annual spending need ($)')
      
      fireEvent.change(portfolioInput, { target: { value: '1000000' } })
      fireEvent.change(spendingInput, { target: { value: '40000' } })
      
      // Should show updated withdrawal rate
      expect(screen.getByText(/\d+\.\d+%/)).toBeInTheDocument()
    })

    it('should show employment income note when value > 0', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      const employmentInput = screen.getByLabelText('Annual employment income ($)')
      fireEvent.change(employmentInput, { target: { value: '50000' } })
      
      expect(screen.getByText(/Until retirement age/)).toBeInTheDocument()
    })
  })

  describe('Market Step', () => {
    it('should show market calibration component', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      
      expect(screen.getByTestId('market-calibration')).toBeInTheDocument()
    })

    it('should show stock projection preview', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      
      expect(screen.getByTestId('stock-projection')).toBeInTheDocument()
      expect(screen.getByText(/7% return, 18% volatility/)).toBeInTheDocument()
    })
  })

  describe('Review Step', () => {
    it('should display all entered information', () => {
      render(<AppWizard />)
      
      // Navigate to review
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      
      expect(screen.getByText('Review your assumptions')).toBeInTheDocument()
      expect(screen.getByText('Demographics')).toBeInTheDocument()
      expect(screen.getByText('Finances')).toBeInTheDocument()
      expect(screen.getByText('Market assumptions')).toBeInTheDocument()
      expect(screen.getByText('Key metrics')).toBeInTheDocument()
    })

    it('should show ready to simulate message', () => {
      render(<AppWizard />)
      
      // Navigate to review
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      
      expect(screen.getByText(/Ready to simulate:/)).toBeInTheDocument()
      expect(screen.getByText(/1,000 Monte Carlo simulations/)).toBeInTheDocument()
    })
  })

  describe('Running Step', () => {
    it('should show progress when simulation starts', async () => {
      render(<AppWizard />)
      
      // Navigate to review
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      
      // Start simulation
      fireEvent.click(screen.getByText('Run simulation'))
      
      expect(screen.getByText('Running simulation...')).toBeInTheDocument()
      expect(screen.getByText(/Year \d+ of \d+/)).toBeInTheDocument()
    })

    it('should show year-by-year progress table', async () => {
      render(<AppWizard />)
      
      // Navigate and start simulation
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      fireEvent.click(screen.getByText('Run simulation'))
      
      await waitFor(() => {
        expect(screen.getByText('Age')).toBeInTheDocument()
        expect(screen.getByText('Portfolio')).toBeInTheDocument()
        expect(screen.getByText('Consumption')).toBeInTheDocument()
        expect(screen.getByText('Taxes')).toBeInTheDocument()
        expect(screen.getByText('Status')).toBeInTheDocument()
      })
    })
  })

  describe('Results Step', () => {
    it('should show simulation results after completion', async () => {
      const { runBatchSimulation } = await import('./services/api')
      vi.mocked(runBatchSimulation).mockResolvedValueOnce({
        results: {
          stocks_only: {
            success_rate: 0.853,
            median_final_portfolio: 1200000,
            failure_risk_10y: 0.052,
            median_failure_age: 87
          }
        }
      })

      render(<AppWizard />)
      
      // Navigate and start simulation
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      fireEvent.click(screen.getByText('Run simulation'))
      
      await waitFor(() => {
        expect(screen.getByText('Simulation results')).toBeInTheDocument()
      }, { timeout: 5000 })
      
      expect(screen.getByText('85.3%')).toBeInTheDocument()
      expect(screen.getByText('$1.2M')).toBeInTheDocument()
    })

    it('should have start over and export buttons', async () => {
      render(<AppWizard />)
      
      // Navigate to results (mock immediate completion)
      fireEvent.click(screen.getByText('Next: Finances'))
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      fireEvent.click(screen.getByText('Next: Review assumptions'))
      fireEvent.click(screen.getByText('Run simulation'))
      
      await waitFor(() => {
        expect(screen.getByText('Simulation results')).toBeInTheDocument()
      }, { timeout: 5000 })
      
      expect(screen.getByText('Start over')).toBeInTheDocument()
      expect(screen.getByText('Export results')).toBeInTheDocument()
    })
  })

  describe('Validation', () => {
    it('should validate demographics before proceeding', () => {
      render(<AppWizard />)
      
      const ageInput = screen.getByLabelText('Current age')
      const maxAgeInput = screen.getByLabelText('Planning to age')
      const nextButton = screen.getByText('Next: Finances')
      
      // Set invalid ages (current > max)
      fireEvent.change(ageInput, { target: { value: '95' } })
      fireEvent.change(maxAgeInput, { target: { value: '90' } })
      
      expect(nextButton).toBeDisabled()
    })

    it('should validate finances before proceeding', () => {
      render(<AppWizard />)
      fireEvent.click(screen.getByText('Next: Finances'))
      
      const spendingInput = screen.getByLabelText('Annual spending need ($)')
      const nextButton = screen.getByText('Next: Market assumptions')
      
      // Set invalid spending (0)
      fireEvent.change(spendingInput, { target: { value: '0' } })
      
      expect(nextButton).toBeDisabled()
      
      // Set valid spending
      fireEvent.change(spendingInput, { target: { value: '60000' } })
      
      expect(nextButton).not.toBeDisabled()
    })
  })

  describe('Page Title Updates', () => {
    it('should update page title based on current step', () => {
      render(<AppWizard />)
      
      expect(document.title).toBe('FinSim - Demographics')
      
      fireEvent.click(screen.getByText('Next: Finances'))
      expect(document.title).toBe('FinSim - Finances')
      
      fireEvent.click(screen.getByText('Next: Market assumptions'))
      expect(document.title).toBe('FinSim - Market Assumptions')
    })
  })
})