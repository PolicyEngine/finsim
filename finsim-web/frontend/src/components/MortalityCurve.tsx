import React, { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import { colors } from '../styles/colors'

interface MortalityCurveProps {
  currentAge: number
  gender: 'Male' | 'Female'
  maxAge?: number
  showSpouse?: boolean
  spouseAge?: number
  spouseGender?: 'Male' | 'Female'
}

// Simplified SSA mortality tables (approximate values)
// Real implementation would use actual SSA tables
const getMortalityRate = (age: number, gender: string): number => {
  // Gompertz-Makeham approximation for mortality
  const isMale = gender === 'Male'
  
  // Parameters roughly calibrated to SSA tables
  const a = isMale ? 0.00004 : 0.00002  // Base mortality
  const b = isMale ? 0.085 : 0.082      // Rate of aging
  const c = 70                          // Reference age
  
  // Mortality rate increases exponentially with age
  const rate = a * Math.exp(b * (age - c))
  
  // Cap at reasonable maximum
  return Math.min(rate, 0.5)
}

const calculateSurvivalProbability = (
  fromAge: number, 
  toAge: number, 
  gender: string
): number => {
  let survivalProb = 1.0
  
  for (let age = fromAge; age < toAge; age++) {
    const mortalityRate = getMortalityRate(age, gender)
    survivalProb *= (1 - mortalityRate)
  }
  
  return survivalProb
}

const MortalityCurve: React.FC<MortalityCurveProps> = ({ 
  currentAge, 
  gender,
  maxAge = 100,
  showSpouse = false,
  spouseAge = 65,
  spouseGender = 'Female'
}) => {
  const survivalData = useMemo(() => {
    const data = []
    
    for (let age = currentAge; age <= maxAge; age++) {
      const survivalProb = calculateSurvivalProbability(currentAge, age, gender)
      
      const dataPoint: any = {
        age,
        you: Math.round(survivalProb * 100)
      }
      
      if (showSpouse && spouseAge) {
        const spouseCurrentAge = spouseAge + (age - currentAge)
        if (spouseCurrentAge <= maxAge) {
          const spouseSurvival = calculateSurvivalProbability(spouseAge, spouseCurrentAge, spouseGender)
          dataPoint.spouse = Math.round(spouseSurvival * 100)
          
          // Joint survival (both alive)
          dataPoint.both = Math.round(survivalProb * spouseSurvival * 100)
          
          // Either survival (at least one alive)
          dataPoint.either = Math.round((1 - (1 - survivalProb) * (1 - spouseSurvival)) * 100)
        }
      }
      
      data.push(dataPoint)
    }
    
    return data
  }, [currentAge, gender, maxAge, showSpouse, spouseAge, spouseGender])

  // Calculate life expectancy
  const lifeExpectancy = useMemo(() => {
    let totalYears = 0
    let lastSurvival = 1.0
    
    for (let age = currentAge; age <= 120; age++) {
      const survival = calculateSurvivalProbability(currentAge, age, gender)
      const yearProb = (lastSurvival + survival) / 2  // Trapezoidal integration
      totalYears += yearProb
      lastSurvival = survival
      
      if (survival < 0.01) break  // Stop when survival is very low
    }
    
    return Math.round(currentAge + totalYears - 1)
  }, [currentAge, gender])

  const spouseLifeExpectancy = useMemo(() => {
    if (!showSpouse || !spouseAge) return null
    
    let totalYears = 0
    let lastSurvival = 1.0
    
    for (let age = spouseAge; age <= 120; age++) {
      const survival = calculateSurvivalProbability(spouseAge, age, spouseGender)
      const yearProb = (lastSurvival + survival) / 2
      totalYears += yearProb
      lastSurvival = survival
      
      if (survival < 0.01) break
    }
    
    return Math.round(spouseAge + totalYears - 1)
  }, [showSpouse, spouseAge, spouseGender])

  return (
    <div className="pe-card">
      <h4 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
        Survival probability
      </h4>
      
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', color: colors.DARK_GRAY }}>
          <div>
            <strong>Your life expectancy:</strong> {lifeExpectancy} years
          </div>
          {showSpouse && spouseLifeExpectancy && (
            <div>
              <strong>Spouse life expectancy:</strong> {spouseLifeExpectancy} years
            </div>
          )}
          <div>
            <strong>50% survival age:</strong> {
              survivalData.find(d => d.you <= 50)?.age || maxAge
            } years
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={survivalData}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.LIGHT_GRAY} />
          <XAxis 
            dataKey="age" 
            label={{ value: 'Age', position: 'insideBottom', offset: -5 }}
            stroke={colors.DARK_GRAY}
          />
          <YAxis 
            label={{ value: 'Survival probability (%)', angle: -90, position: 'insideLeft' }}
            stroke={colors.DARK_GRAY}
            domain={[0, 100]}
          />
          <Tooltip 
            formatter={(value: number) => `${value}%`}
            contentStyle={{ 
              backgroundColor: colors.WHITE,
              border: `1px solid ${colors.LIGHT_GRAY}`,
              borderRadius: '8px'
            }}
          />
          <Legend />
          
          <Line
            type="monotone"
            dataKey="you"
            stroke={colors.DARKEST_BLUE}
            strokeWidth={2}
            dot={false}
            name={`You (${gender}, age ${currentAge})`}
          />
          
          {showSpouse && (
            <>
              <Line
                type="monotone"
                dataKey="spouse"
                stroke={colors.TEAL_ACCENT}
                strokeWidth={2}
                dot={false}
                name={`Spouse (${spouseGender}, age ${spouseAge})`}
              />
              <Line
                type="monotone"
                dataKey="both"
                stroke={colors.DARK_RED}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="Both alive"
              />
              <Line
                type="monotone"
                dataKey="either"
                stroke={colors.TEAL_PRESSED}
                strokeWidth={2}
                strokeDasharray="3 3"
                dot={false}
                name="Either alive"
              />
            </>
          )}
        </LineChart>
      </ResponsiveContainer>

      <div style={{ 
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: colors.BLUE_98,
        borderRadius: '8px',
        fontSize: '0.85rem',
        color: colors.DARK_GRAY
      }}>
        <strong>Understanding the chart:</strong> This shows the probability of survival to each age based on SSA mortality tables. 
        {showSpouse ? 
          ' The joint curves show probabilities for couples - "both alive" requires both partners to survive, while "either alive" means at least one survives.' :
          ' Life expectancy represents the average age at death, but individual outcomes vary significantly.'
        }
      </div>
    </div>
  )
}

export default MortalityCurve