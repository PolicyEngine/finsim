import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
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

describe('App Layout Consistency', () => {
  it('should have consistent content width across all tabs', () => {
    const { getByText, getByTestId } = render(<App />)
    
    // Get the content wrapper
    const contentWrapper = getByTestId('content-wrapper')
    
    // Check initial assumptions tab width
    const assumptionsWidth = contentWrapper.offsetWidth
    const assumptionsComputedStyle = window.getComputedStyle(contentWrapper)
    const assumptionsPadding = assumptionsComputedStyle.padding
    
    // Switch to Results tab
    fireEvent.click(getByText('Results'))
    const resultsWidth = contentWrapper.offsetWidth
    const resultsComputedStyle = window.getComputedStyle(contentWrapper)
    const resultsPadding = resultsComputedStyle.padding
    
    // Switch to Analysis tab
    fireEvent.click(getByText('Analysis'))
    const analysisWidth = contentWrapper.offsetWidth
    const analysisComputedStyle = window.getComputedStyle(contentWrapper)
    const analysisPadding = analysisComputedStyle.padding
    
    // Switch to Strategy tab
    fireEvent.click(getByText('Strategy'))
    const strategyWidth = contentWrapper.offsetWidth
    const strategyComputedStyle = window.getComputedStyle(contentWrapper)
    const strategyPadding = strategyComputedStyle.padding
    
    // Switch to Methodology tab
    fireEvent.click(getByText('Methodology'))
    const methodologyWidth = contentWrapper.offsetWidth
    const methodologyComputedStyle = window.getComputedStyle(contentWrapper)
    const methodologyPadding = methodologyComputedStyle.padding
    
    // All widths should be equal
    expect(resultsWidth).toBe(assumptionsWidth)
    expect(analysisWidth).toBe(assumptionsWidth)
    expect(strategyWidth).toBe(assumptionsWidth)
    expect(methodologyWidth).toBe(assumptionsWidth)
    
    // All padding should be consistent
    expect(resultsPadding).toBe(assumptionsPadding)
    expect(analysisPadding).toBe(assumptionsPadding)
    expect(strategyPadding).toBe(assumptionsPadding)
    expect(methodologyPadding).toBe(assumptionsPadding)
    
    console.log('Layout consistency test results:')
    console.log(`All tab widths: ${assumptionsWidth}px`)
    console.log(`All tab padding: ${assumptionsPadding}`)
  })
  
  it('should not have any container class restricting width', () => {
    const { container } = render(<App />)
    
    // Check that no element has the 'container' class
    const elementsWithContainer = container.querySelectorAll('.container')
    expect(elementsWithContainer.length).toBe(0)
  })
  
  it('should use full viewport width', () => {
    const { getByTestId } = render(<App />)
    
    const contentWrapper = getByTestId('content-wrapper')
    const computedStyle = window.getComputedStyle(contentWrapper)
    
    // Should have width: 100%
    expect(computedStyle.width).toBeTruthy()
    expect(computedStyle.maxWidth).toBe('100%')
  })
})