import React from 'react'
import { colors } from '../styles/colors'

interface ConfidenceData {
  [scenarioId: string]: {
    [confidenceLevel: string]: number
  }
}

interface ConfidenceTableProps {
  data: ConfidenceData
  scenarioNames: { [id: string]: string }
  confidenceLevels: number[]
}

const ConfidenceTable: React.FC<ConfidenceTableProps> = ({ 
  data, 
  scenarioNames,
  confidenceLevels 
}) => {
  const getBestScenario = (confidenceLevel: number) => {
    let bestScenario = ''
    let bestValue = 0

    Object.entries(data).forEach(([scenarioId, values]) => {
      const value = values[confidenceLevel.toString()]
      if (value > bestValue) {
        bestValue = value
        bestScenario = scenarioId
      }
    })

    return bestScenario
  }

  return (
    <div className="pe-card">
      <h3 style={{ marginBottom: '1rem' }}>Sustainable Spending by Confidence Level</h3>
      
      <div style={{ overflowX: 'auto' }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          fontSize: '0.95rem'
        }}>
          <thead>
            <tr style={{ backgroundColor: colors.BLUE_98 }}>
              <th style={{ 
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: `2px solid ${colors.BLUE_LIGHT}`,
                color: colors.DARKEST_BLUE,
                fontWeight: 600
              }}>
                Scenario
              </th>
              {confidenceLevels.map(level => (
                <th key={level} style={{ 
                  padding: '0.75rem',
                  textAlign: 'right',
                  borderBottom: `2px solid ${colors.BLUE_LIGHT}`,
                  color: colors.DARKEST_BLUE,
                  fontWeight: 600
                }}>
                  {level}% Confidence
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(data).map(([scenarioId, values]) => {
              const scenarioName = scenarioNames[scenarioId] || scenarioId
              
              return (
                <tr key={scenarioId} style={{ 
                  borderBottom: `1px solid ${colors.LIGHT_GRAY}`,
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = colors.BLUE_98
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}>
                  <td style={{ 
                    padding: '0.75rem',
                    fontWeight: 500,
                    color: colors.DARKEST_BLUE
                  }}>
                    {scenarioName}
                  </td>
                  {confidenceLevels.map(level => {
                    const value = values[level.toString()]
                    const isBest = getBestScenario(level) === scenarioId
                    
                    return (
                      <td key={level} style={{ 
                        padding: '0.75rem',
                        textAlign: 'right',
                        fontWeight: isBest ? 600 : 400,
                        color: isBest ? colors.TEAL_ACCENT : colors.DARK_GRAY,
                        backgroundColor: isBest ? colors.TEAL_LIGHT : 'transparent'
                      }}>
                        ${value?.toLocaleString() || 'N/A'}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      
      <div style={{ 
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: colors.BLUE_98,
        borderRadius: '8px'
      }}>
        <p style={{ 
          fontSize: '0.875rem', 
          color: colors.DARK_GRAY,
          margin: 0
        }}>
          <strong>Note:</strong> Values shown are annual spending amounts in 2025 dollars. 
          Higher confidence levels represent more conservative spending strategies.
        </p>
      </div>
    </div>
  )
}

export default ConfidenceTable