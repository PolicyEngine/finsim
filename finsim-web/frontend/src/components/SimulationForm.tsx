import React, { useState } from 'react'
import type { SimulationParameters } from '../services/api'

interface SimulationFormProps {
  onSubmit: (data: SimulationParameters & { spending_level: number }) => void
  isSubmitting?: boolean
}

const SimulationForm: React.FC<SimulationFormProps> = ({ onSubmit, isSubmitting = false }) => {
  const [formData, setFormData] = useState({
    current_age: 65,
    gender: 'Male',
    social_security: 24000,
    state: 'CA',
    expected_return: 7,
    return_volatility: 18,
    dividend_yield: 1.8,
    spending_level: 0,
  })

  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    const numericFields = ['current_age', 'social_security', 'expected_return', 'return_volatility', 'dividend_yield', 'spending_level']
    
    setFormData(prev => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value
    }))

    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validate = () => {
    const newErrors: { [key: string]: string } = {}

    if (!formData.spending_level || formData.spending_level <= 0) {
      newErrors.spending_level = 'Spending level is required and must be positive'
    }

    if (formData.current_age < 18 || formData.current_age > 100) {
      newErrors.current_age = 'Age must be between 18 and 100'
    }

    if (formData.social_security < 0) {
      newErrors.social_security = 'Social Security cannot be negative'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (validate()) {
      onSubmit(formData)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="pe-card">
      <h3 style={{ marginBottom: '1.5rem' }}>Simulation Parameters</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label htmlFor="current_age" className="pe-label">
            Current Age
          </label>
          <input
            type="number"
            id="current_age"
            name="current_age"
            value={formData.current_age}
            onChange={handleChange}
            className="pe-input"
            min="18"
            max="100"
          />
          {errors.current_age && <div className="pe-error">{errors.current_age}</div>}
        </div>

        <div>
          <label htmlFor="gender" className="pe-label">
            Gender
          </label>
          <select
            id="gender"
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className="pe-select"
          >
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>

        <div>
          <label htmlFor="social_security" className="pe-label">
            Social Security (Annual)
          </label>
          <input
            type="number"
            id="social_security"
            name="social_security"
            value={formData.social_security}
            onChange={handleChange}
            className="pe-input"
            min="0"
            step="1000"
          />
          {errors.social_security && <div className="pe-error">{errors.social_security}</div>}
        </div>

        <div>
          <label htmlFor="state" className="pe-label">
            State
          </label>
          <select
            id="state"
            name="state"
            value={formData.state}
            onChange={handleChange}
            className="pe-select"
          >
            <option value="CA">California</option>
            <option value="NY">New York</option>
            <option value="TX">Texas</option>
            <option value="FL">Florida</option>
            <option value="WA">Washington</option>
            <option value="NV">Nevada</option>
            <option value="IL">Illinois</option>
            <option value="MA">Massachusetts</option>
          </select>
        </div>

        <div>
          <label htmlFor="expected_return" className="pe-label">
            Expected Return (%)
          </label>
          <input
            type="number"
            id="expected_return"
            name="expected_return"
            value={formData.expected_return}
            onChange={handleChange}
            className="pe-input"
            min="0"
            max="20"
            step="0.5"
          />
        </div>

        <div>
          <label htmlFor="return_volatility" className="pe-label">
            Return Volatility (%)
          </label>
          <input
            type="number"
            id="return_volatility"
            name="return_volatility"
            value={formData.return_volatility}
            onChange={handleChange}
            className="pe-input"
            min="0"
            max="50"
            step="0.5"
          />
        </div>

        <div>
          <label htmlFor="dividend_yield" className="pe-label">
            Dividend Yield (%)
          </label>
          <input
            type="number"
            id="dividend_yield"
            name="dividend_yield"
            value={formData.dividend_yield}
            onChange={handleChange}
            className="pe-input"
            min="0"
            max="10"
            step="0.1"
          />
        </div>

        <div>
          <label htmlFor="spending_level" className="pe-label">
            Annual Spending ($)
          </label>
          <input
            type="number"
            id="spending_level"
            name="spending_level"
            value={formData.spending_level || ''}
            onChange={handleChange}
            className="pe-input"
            min="0"
            step="5000"
            placeholder="50000"
          />
          {errors.spending_level && <div className="pe-error">{errors.spending_level}</div>}
        </div>
      </div>

      <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
        <button
          type="submit"
          className="pe-button-primary"
          disabled={isSubmitting}
          style={{ minWidth: '150px' }}
        >
          {isSubmitting ? (
            <>
              <span className="pe-loading" style={{ 
                display: 'inline-block', 
                marginRight: '0.5rem',
                width: '16px',
                height: '16px',
                verticalAlign: 'middle' 
              }}></span>
              Running...
            </>
          ) : (
            'Run Simulation'
          )}
        </button>
      </div>
    </form>
  )
}

export default SimulationForm