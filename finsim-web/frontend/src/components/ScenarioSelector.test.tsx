import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ScenarioSelector from './ScenarioSelector'
import { getScenarios } from '../services/api'

// Mock the API service
vi.mock('../services/api', () => ({
  getScenarios: vi.fn()
}))

describe('ScenarioSelector', () => {
  const mockScenarios = [
    {
      id: 'stocks_only',
      name: '100% Stocks (VT)',
      description: 'Full investment in globally diversified stock index',
      has_annuity: false,
      initial_portfolio: 677530,
      annuity_annual: 0,
      annuity_type: undefined,
      annuity_guarantee_years: 0
    },
    {
      id: 'annuity_a',
      name: 'Annuity A + Stocks',
      description: 'Life annuity with 15-year guarantee plus stocks',
      has_annuity: true,
      initial_portfolio: 150000,
      annuity_annual: 42195,
      annuity_type: 'Life Contingent with Guarantee',
      annuity_guarantee_years: 15
    }
  ]

  it('should load and display scenarios', async () => {
    vi.mocked(getScenarios).mockResolvedValue(mockScenarios)
    
    render(<ScenarioSelector onSelect={vi.fn()} />)
    
    await waitFor(() => {
      expect(screen.getByText('100% Stocks (VT)')).toBeInTheDocument()
      expect(screen.getByText('Annuity A + Stocks')).toBeInTheDocument()
    })
  })

  it('should call onSelect when scenario is selected', async () => {
    const onSelect = vi.fn()
    vi.mocked(getScenarios).mockResolvedValue(mockScenarios)
    
    render(<ScenarioSelector onSelect={onSelect} />)
    
    await waitFor(() => {
      const stocksOption = screen.getByText('100% Stocks (VT)')
      fireEvent.click(stocksOption)
    })
    
    expect(onSelect).toHaveBeenCalledWith('stocks_only')
  })

  it('should show loading state while fetching', () => {
    vi.mocked(getScenarios).mockImplementation(() => new Promise(() => {}))
    
    render(<ScenarioSelector onSelect={vi.fn()} />)
    
    expect(screen.getByText('Loading scenarios...')).toBeInTheDocument()
  })

  it('should show error if scenarios fail to load', async () => {
    vi.mocked(getScenarios).mockRejectedValue(new Error('Failed to load'))
    
    render(<ScenarioSelector onSelect={vi.fn()} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load scenarios/)).toBeInTheDocument()
    })
  })
})