import React, { useEffect, useState } from 'react'
import { getScenarios } from '../services/api'
import type { Scenario } from '../services/api'
import { colors } from '../styles/colors'

interface ScenarioSelectorProps {
  onSelect: (scenarioId: string) => void
  selectedIds?: string[]
  multiple?: boolean
}

const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({ 
  onSelect, 
  selectedIds = [],
  multiple = false 
}) => {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        setLoading(true)
        const data = await getScenarios()
        setScenarios(data)
        setError(null)
      } catch (err) {
        setError('Failed to load scenarios')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchScenarios()
  }, [])

  if (loading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center' }}>
        <div className="pe-loading" style={{ margin: '0 auto' }}></div>
        <p style={{ marginTop: '1rem' }}>Loading scenarios...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '1rem', color: colors.DARK_RED }}>
        {error}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h3>Select Scenario{multiple ? 's' : ''}</h3>
      {scenarios.map((scenario) => {
        const isSelected = selectedIds.includes(scenario.id)
        
        return (
          <div
            key={scenario.id}
            className="pe-card"
            style={{
              cursor: 'pointer',
              border: isSelected ? `2px solid ${colors.TEAL_ACCENT}` : '2px solid transparent',
              backgroundColor: isSelected ? colors.TEAL_LIGHT : colors.WHITE,
            }}
            onClick={() => onSelect(scenario.id)}
          >
            <h4 style={{ marginBottom: '0.5rem', color: colors.DARKEST_BLUE }}>
              {scenario.name}
            </h4>
            <p style={{ color: colors.DARK_GRAY, fontSize: '0.875rem' }}>
              {scenario.description}
            </p>
            {scenario.has_annuity && (
              <div style={{ marginTop: '0.5rem' }}>
                <span style={{ 
                  backgroundColor: colors.BLUE_LIGHT, 
                  color: colors.BLUE,
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontWeight: 500
                }}>
                  Includes Annuity
                </span>
                {scenario.annuity_annual && (
                  <span style={{ marginLeft: '0.5rem', color: colors.DARK_GRAY }}>
                    ${scenario.annuity_annual.toLocaleString()}/year
                  </span>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ScenarioSelector