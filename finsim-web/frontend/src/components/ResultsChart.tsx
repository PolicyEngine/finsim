import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { colors } from '../styles/colors'

interface ChartData {
  spending: number
  [key: string]: number
}

interface ResultsChartProps {
  data: ChartData[]
  scenarios: string[]
  confidenceLevel?: number
}

const scenarioColors = [
  colors.TEAL_ACCENT,
  colors.BLUE,
  colors.DARK_RED,
  colors.DARK_GRAY,
]

const ResultsChart: React.FC<ResultsChartProps> = ({ data, scenarios }) => {
  return (
    <div className="pe-card">
      <h3 style={{ marginBottom: '1rem' }}>Success Rate by Annual Spending</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={colors.LIGHT_GRAY} />
          <XAxis 
            dataKey="spending"
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            stroke={colors.DARK_GRAY}
          />
          <YAxis 
            tickFormatter={(value) => `${value}%`}
            domain={[0, 100]}
            stroke={colors.DARK_GRAY}
          />
          <Tooltip
            formatter={(value: number) => `${value.toFixed(1)}%`}
            labelFormatter={(label) => `Spending: $${Number(label).toLocaleString()}`}
          />
          <Legend />
          
          {/* Reference lines for common confidence levels */}
          <ReferenceLine 
            y={90} 
            stroke={colors.MEDIUM_LIGHT_GRAY} 
            strokeDasharray="5 5"
            label="90% confidence"
          />
          <ReferenceLine 
            y={75} 
            stroke={colors.MEDIUM_LIGHT_GRAY} 
            strokeDasharray="5 5"
            label="75% confidence"
          />
          <ReferenceLine 
            y={50} 
            stroke={colors.MEDIUM_LIGHT_GRAY} 
            strokeDasharray="5 5"
            label="50% confidence"
          />
          
          {scenarios.map((scenario, index) => (
            <Line
              key={scenario}
              type="monotone"
              dataKey={scenario}
              stroke={scenarioColors[index % scenarioColors.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
              name={scenario}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      
      <p style={{ 
        marginTop: '1rem', 
        fontSize: '0.875rem', 
        color: colors.DARK_GRAY,
        textAlign: 'center' 
      }}>
        Higher success rates indicate more sustainable spending levels
      </p>
    </div>
  )
}

export default ResultsChart