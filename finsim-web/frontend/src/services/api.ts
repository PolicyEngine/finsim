import axios from 'axios'

// Use relative URLs so Vite proxy handles the routing
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Scenario {
  id: string
  name: string
  description: string
  has_annuity: boolean
  initial_portfolio: number
  annuity_annual?: number
  annuity_type?: string
  annuity_guarantee_years?: number
}

export interface SimulationParameters {
  current_age: number
  gender: string
  social_security: number
  state: string
  expected_return: number
  return_volatility: number
  dividend_yield?: number
  pension?: number
  employment_income?: number
  retirement_age?: number
  include_mortality?: boolean
}

export interface SimulationRequest {
  scenario_id: string
  spending_level: number
  parameters: SimulationParameters
}

export interface BatchSimulationRequest {
  scenario_ids: string[]
  spending_levels: number[]
  parameters: SimulationParameters
}

export interface SimulationResult {
  success_rate: number
  median_final: number
  p10_final: number
  p90_final: number
  years_survived_median?: number
  years_survived_p10?: number
  years_survived_p90?: number
}

export interface BatchSimulationResult {
  scenario: string
  scenario_name: string
  spending: number
  success_rate: number
  median_final: number
  p10_final: number
  p90_final: number
}

export interface ConfidenceAnalysisRequest {
  scenario_ids: string[]
  confidence_levels: number[]
  parameters: SimulationParameters
}

export interface ConfidenceAnalysisResult {
  [scenarioId: string]: {
    [confidenceLevel: string]: number
  }
}

export const getScenarios = async (): Promise<Scenario[]> => {
  const response = await api.get('/scenarios')
  return response.data.scenarios
}

export const getScenario = async (id: string): Promise<Scenario> => {
  const response = await api.get(`/scenarios/${id}`)
  return response.data
}

export const runSimulation = async (request: SimulationRequest): Promise<SimulationResult> => {
  const response = await api.post('/simulate', request)
  return response.data.results
}

export const runBatchSimulation = async (request: BatchSimulationRequest): Promise<BatchSimulationResult[]> => {
  const response = await api.post('/simulate/batch', request)
  return response.data.results
}

export const analyzeConfidence = async (request: ConfidenceAnalysisRequest): Promise<ConfidenceAnalysisResult> => {
  const response = await api.post('/analyze/confidence', request)
  return response.data.results
}

export const exportResults = async (results: any[], format: 'csv' | 'json' = 'csv'): Promise<Blob> => {
  const response = await api.post('/export', 
    { results, format },
    { responseType: 'blob' }
  )
  return response.data
}