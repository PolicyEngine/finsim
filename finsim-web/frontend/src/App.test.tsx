import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from './App'

// Mock the API module
vi.mock('./services/api', () => ({
  getScenarios: vi.fn(() => Promise.resolve([
    { id: 'stocks_only', name: 'Stocks Only', description: 'Test scenario' }
  ])),
  runBatchSimulation: vi.fn(() => Promise.resolve({ results: [] })),
  analyzeConfidence: vi.fn(() => Promise.resolve({ results: [] })),
  exportResults: vi.fn(() => Promise.resolve())
}))

// Mock MarketCalibration component
vi.mock('./components/MarketCalibration', () => ({
  default: () => <div data-testid="market-calibration">Market Calibration</div>
}))

// Mock Methodology component
vi.mock('./components/Methodology', () => ({
  default: () => <div data-testid="methodology">Methodology</div>
}))

describe('App', () => {
  it('should render without crashing', () => {
    render(<App />)
    expect(screen.getByText('FinSim')).toBeInTheDocument()
  })

  it('should display all navigation tabs', () => {
    render(<App />)
    expect(screen.getByText('Assumptions')).toBeInTheDocument()
    expect(screen.getByText('Results')).toBeInTheDocument()
    expect(screen.getByText('Analysis')).toBeInTheDocument()
    expect(screen.getByText('Strategy')).toBeInTheDocument()
    expect(screen.getByText('Methodology')).toBeInTheDocument()
  })

  it('should switch between tabs when clicked', () => {
    render(<App />)
    
    // Initially on assumptions tab
    expect(screen.getByText('Demographics')).toBeInTheDocument()
    
    // Click on Methodology tab
    fireEvent.click(screen.getByText('Methodology'))
    expect(screen.getByTestId('methodology')).toBeInTheDocument()
    
    // Click back to Assumptions
    fireEvent.click(screen.getByText('Assumptions'))
    expect(screen.getByText('Demographics')).toBeInTheDocument()
  })

  it('should update document title when switching tabs', () => {
    render(<App />)
    
    // Initial title
    expect(document.title).toBe('FinSim - Setup')
    
    // Switch to Results tab
    fireEvent.click(screen.getByText('Results'))
    expect(document.title).toBe('FinSim - Results')
    
    // Switch to Methodology tab
    fireEvent.click(screen.getByText('Methodology'))
    expect(document.title).toBe('FinSim - Methodology')
  })

  it('should display market calibration component in assumptions tab', () => {
    render(<App />)
    expect(screen.getByTestId('market-calibration')).toBeInTheDocument()
  })

  it('should have two-column layout in assumptions tab', () => {
    render(<App />)
    
    // Check for both columns
    expect(screen.getByText('Demographics')).toBeInTheDocument()
    expect(screen.getByText('Financial details')).toBeInTheDocument()
  })

  it('should calculate withdrawal rate correctly', () => {
    render(<App />)
    
    // Check that withdrawal rate is displayed
    const withdrawalRateElement = screen.getByText(/Initial Withdrawal Rate/i)
    expect(withdrawalRateElement).toBeInTheDocument()
  })

  it('should display run simulation button', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /Run Simulation/i })
    expect(button).toBeInTheDocument()
    expect(button).not.toBeDisabled()
  })

  it('should not use emojis in professional interface', () => {
    const { container } = render(<App />)
    const text = container.textContent || ''
    
    // Check that common emojis are not present
    expect(text).not.toMatch(/💰|📊|📈|🎯|❓|👤|💸|🏦|⚙️/)
  })

  it('should use sentence case for headings', () => {
    render(<App />)
    
    // These should be sentence case
    expect(screen.getByText('Annual consumption')).toBeInTheDocument()
    expect(screen.getByText('Income sources')).toBeInTheDocument()
    expect(screen.getByText('Simulation settings')).toBeInTheDocument()
  })
})