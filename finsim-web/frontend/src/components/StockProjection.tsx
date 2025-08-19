import React, { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart, Legend
} from 'recharts'
import { colors } from '../styles/colors'

interface StockProjectionProps {
  expectedReturn: number
  volatility: number
  currentValue?: number
  years?: number
}

const StockProjection: React.FC<StockProjectionProps> = ({ 
  expectedReturn, 
  volatility,
  currentValue = 100,
  years = 30
}) => {
  const projectionData = useMemo(() => {
    const data = []
    const annualReturn = expectedReturn / 100
    const annualVolatility = volatility / 100
    
    for (let year = 0; year <= years; year++) {
      const timeHorizon = year
      const expectedValue = currentValue * Math.exp(annualReturn * timeHorizon)
      
      // Calculate confidence intervals using log-normal distribution
      // For log-normal: variance grows with time
      const variance = annualVolatility * annualVolatility * timeHorizon
      const stdDev = Math.sqrt(variance)
      
      // Log-normal percentiles
      const median = currentValue * Math.exp((annualReturn - 0.5 * annualVolatility * annualVolatility) * timeHorizon)
      const p95 = currentValue * Math.exp((annualReturn - 0.5 * annualVolatility * annualVolatility) * timeHorizon + 1.645 * stdDev)
      const p75 = currentValue * Math.exp((annualReturn - 0.5 * annualVolatility * annualVolatility) * timeHorizon + 0.674 * stdDev)
      const p25 = currentValue * Math.exp((annualReturn - 0.5 * annualVolatility * annualVolatility) * timeHorizon - 0.674 * stdDev)
      const p5 = currentValue * Math.exp((annualReturn - 0.5 * annualVolatility * annualVolatility) * timeHorizon - 1.645 * stdDev)
      
      data.push({
        year,
        expected: Math.round(expectedValue),
        median: Math.round(median),
        p95: Math.round(p95),
        p75: Math.round(p75),
        p25: Math.round(p25),
        p5: Math.round(p5)
      })
    }
    
    return data
  }, [expectedReturn, volatility, currentValue, years])

  const formatValue = (value: number) => {
    if (currentValue === 100) {
      return `$${value}`
    }
    return `$${(value / 1000).toFixed(0)}k`
  }

  const formatTooltipValue = (value: number) => {
    if (currentValue === 100) {
      return `$${value.toLocaleString()}`
    }
    return `$${value.toLocaleString()}`
  }

  return (
    <div className="pe-card">
      <h4 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
        Projected growth path
      </h4>
      
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', color: colors.DARK_GRAY }}>
          <div>
            <strong>Expected return:</strong> {expectedReturn.toFixed(1)}% annually
          </div>
          <div>
            <strong>Volatility:</strong> {volatility.toFixed(1)}%
          </div>
          <div>
            <strong>Starting value:</strong> ${currentValue === 100 ? '100' : currentValue.toLocaleString()}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={projectionData}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.LIGHT_GRAY} />
          <XAxis 
            dataKey="year" 
            label={{ value: 'Years from now', position: 'insideBottom', offset: -5 }}
            stroke={colors.DARK_GRAY}
          />
          <YAxis 
            tickFormatter={formatValue}
            label={{ value: currentValue === 100 ? 'Value ($)' : 'Portfolio value', angle: -90, position: 'insideLeft' }}
            stroke={colors.DARK_GRAY}
          />
          <Tooltip 
            formatter={(value: number) => formatTooltipValue(value)}
            contentStyle={{ 
              backgroundColor: colors.WHITE,
              border: `1px solid ${colors.LIGHT_GRAY}`,
              borderRadius: '8px'
            }}
          />
          <Legend />
          
          {/* 90% confidence interval (5th to 95th percentile) */}
          <Area
            type="monotone"
            dataKey="p95"
            stackId="1"
            stroke="none"
            fill={colors.TEAL_LIGHT}
            fillOpacity={0.3}
            name="95th percentile"
          />
          <Area
            type="monotone"
            dataKey="p5"
            stackId="2"
            stroke="none"
            fill={colors.WHITE}
            fillOpacity={1}
            name="5th percentile"
          />
          
          {/* 50% confidence interval (25th to 75th percentile) */}
          <Area
            type="monotone"
            dataKey="p75"
            stackId="3"
            stroke="none"
            fill={colors.TEAL_ACCENT}
            fillOpacity={0.3}
            name="75th percentile"
          />
          <Area
            type="monotone"
            dataKey="p25"
            stackId="4"
            stroke="none"
            fill={colors.WHITE}
            fillOpacity={1}
            name="25th percentile"
          />
          
          {/* Median line */}
          <Line
            type="monotone"
            dataKey="median"
            stroke={colors.DARKEST_BLUE}
            strokeWidth={2}
            dot={false}
            name="Median"
          />
          
          {/* Expected value line */}
          <Line
            type="monotone"
            dataKey="expected"
            stroke={colors.TEAL_PRESSED}
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Expected"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div style={{ 
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: colors.BLUE_98,
        borderRadius: '8px',
        fontSize: '0.85rem',
        color: colors.DARK_GRAY
      }}>
        <strong>Understanding the chart:</strong> The shaded areas show confidence intervals based on historical volatility. 
        The dark band represents 50% confidence (where returns will likely fall half the time), 
        while the light band shows 90% confidence. The wider spread over time reflects increasing uncertainty.
      </div>
    </div>
  )
}

export default StockProjection