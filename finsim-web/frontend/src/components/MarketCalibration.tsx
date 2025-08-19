import React, { useState, useEffect } from 'react'
import { colors } from '../styles/colors'
import axios from 'axios'

interface MarketCalibrationProps {
  onUpdate: (data: MarketData) => void
  ticker?: string
}

interface MarketData {
  expected_return: number
  return_volatility: number
  dividend_yield: number
  years_of_data: number
  // Advanced calibration fields
  return_stderr?: number
  volatility_stderr?: number
  skewness?: number
  excess_kurtosis?: number
  regime_probs?: number[]
  regime_returns?: number[]
  regime_vols?: number[]
  calibration_method?: string
}

const MarketCalibration: React.FC<MarketCalibrationProps> = ({ 
  onUpdate, 
  ticker = 'VT' 
}) => {
  const [loading, setLoading] = useState(false)
  const [marketData, setMarketData] = useState<MarketData>({
    expected_return: 7.0,
    return_volatility: 18.0,
    dividend_yield: 1.8,
    years_of_data: 10
  })
  const [manualOverride, setManualOverride] = useState(false)
  const [lookbackYears, setLookbackYears] = useState(10)
  const [useAllData, setUseAllData] = useState(true)
  const [currentTicker, setCurrentTicker] = useState(ticker)

  const fetchMarketData = async () => {
    setLoading(true)
    console.log('Fetching market data for', currentTicker, 'with lookback', useAllData ? 50 : lookbackYears)
    try {
      const response = await axios.post('/api/market/calibrate', {
        ticker: currentTicker,
        lookback_years: useAllData ? 50 : lookbackYears
      })
      
      const data = response.data
      console.log('API Response:', data)
      
      const updatedData: MarketData = {
        expected_return: data.price_return,
        return_volatility: data.volatility,
        dividend_yield: data.dividend_yield,
        years_of_data: data.actual_years,
        return_stderr: data.return_stderr,
        volatility_stderr: data.volatility_stderr,
        skewness: data.skewness,
        excess_kurtosis: data.excess_kurtosis,
        regime_probs: data.regime_probs,
        regime_returns: data.regime_returns,
        regime_vols: data.regime_vols,
        calibration_method: data.calibration_method
      }
      console.log('Setting marketData to:', updatedData)
      setMarketData(updatedData)
      onUpdate(updatedData)
    } catch (error) {
      console.error('Failed to fetch market data:', error)
      // Use defaults
      onUpdate(marketData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMarketData()
  }, [currentTicker, lookbackYears, useAllData])
  
  // Add console logging for debugging
  useEffect(() => {
    console.log('MarketData updated:', marketData)
  }, [marketData])

  return (
    <div className="pe-card">
      <h3 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
        Market calibration
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label className="pe-label">Index fund ticker</label>
          <input
            type="text"
            value={currentTicker}
            onChange={(e) => setCurrentTicker(e.target.value.toUpperCase())}
            className="pe-input"
            placeholder="VT, VOO, SPY, QQQ"
          />
          <small style={{ color: colors.DARK_GRAY }}>
            Common: VT (2008+), VOO (2010+), SPY (1993+)
          </small>
        </div>

        <div>
          <label className="pe-label">
            <input
              type="checkbox"
              checked={useAllData}
              onChange={(e) => setUseAllData(e.target.checked)}
              style={{ marginRight: '0.5rem' }}
            />
            Use all available data
          </label>
          {!useAllData && (
            <input
              type="number"
              value={lookbackYears}
              onChange={(e) => setLookbackYears(Number(e.target.value))}
              className="pe-input"
              min="3"
              max="50"
              style={{ marginTop: '0.5rem' }}
            />
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="pe-loading"></div>
          <p>Fetching {currentTicker} data...</p>
        </div>
      ) : (
        <div style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          backgroundColor: colors.TEAL_LIGHT,
          borderRadius: '8px'
        }}>
          <h4 style={{ color: colors.TEAL_PRESSED, marginBottom: '0.5rem' }}>
            ✅ {currentTicker} Historical Stats ({marketData.years_of_data}Y available)
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div>
              <small style={{ color: colors.DARK_GRAY }}>Price Return</small>
              <div style={{ fontWeight: 600 }}>{marketData.expected_return.toFixed(1)}%</div>
            </div>
            <div>
              <small style={{ color: colors.DARK_GRAY }}>Dividend yield</small>
              <div style={{ fontWeight: 600 }}>{marketData.dividend_yield.toFixed(1)}%</div>
            </div>
            <div>
              <small style={{ color: colors.DARK_GRAY }}>Total Return</small>
              <div style={{ fontWeight: 600 }}>
                {(marketData.expected_return + marketData.dividend_yield).toFixed(1)}%
              </div>
            </div>
            <div>
              <small style={{ color: colors.DARK_GRAY }}>Volatility</small>
              <div style={{ fontWeight: 600 }}>{marketData.return_volatility.toFixed(1)}%</div>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: '1rem' }}>
        <label className="pe-label">
          <input
            type="checkbox"
            checked={manualOverride}
            onChange={(e) => setManualOverride(e.target.checked)}
            style={{ marginRight: '0.5rem' }}
          />
          Manual Override
        </label>

        {manualOverride && (
          <div style={{ 
            marginTop: '1rem', 
            padding: '1rem', 
            backgroundColor: colors.LIGHT_GRAY,
            borderRadius: '8px'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
              <div>
                <label className="pe-label">Expected return (%)</label>
                <input
                  type="number"
                  value={marketData.expected_return}
                  onChange={(e) => {
                    const newData = { ...marketData, expected_return: Number(e.target.value) }
                    setMarketData(newData)
                    onUpdate(newData)
                  }}
                  className="pe-input"
                  min="0"
                  max="15"
                  step="0.5"
                />
              </div>
              <div>
                <label className="pe-label">Volatility (%)</label>
                <input
                  type="number"
                  value={marketData.return_volatility}
                  onChange={(e) => {
                    const newData = { ...marketData, return_volatility: Number(e.target.value) }
                    setMarketData(newData)
                    onUpdate(newData)
                  }}
                  className="pe-input"
                  min="5"
                  max="30"
                  step="1"
                />
              </div>
              <div>
                <label className="pe-label">Dividend yield (%)</label>
                <input
                  type="number"
                  value={marketData.dividend_yield}
                  onChange={(e) => {
                    const newData = { ...marketData, dividend_yield: Number(e.target.value) }
                    setMarketData(newData)
                    onUpdate(newData)
                  }}
                  className="pe-input"
                  min="0"
                  max="5"
                  step="0.25"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={fetchMarketData}
        className="pe-button-secondary"
        style={{ marginTop: '1rem' }}
        disabled={loading}
      >
        🔄 Refresh Data
      </button>

      {marketData.return_stderr && (
        <div style={{ 
          marginTop: '1rem',
          padding: '0.75rem',
          backgroundColor: colors.BLUE_98,
          borderRadius: '8px',
          fontSize: '0.875rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <small style={{ color: colors.DARK_GRAY }}>Expected return (95% CI)</small>
              <div style={{ fontWeight: 600 }}>
                {marketData.expected_return.toFixed(1)}% 
                <span style={{ color: colors.DARK_GRAY, fontWeight: 400 }}>
                  {' '}± {(marketData.return_stderr * 2).toFixed(1)}%
                </span>
              </div>
            </div>
            {marketData.excess_kurtosis && marketData.excess_kurtosis > 1 && (
              <div style={{ 
                padding: '0.25rem 0.5rem',
                backgroundColor: colors.LIGHT_ORANGE,
                borderRadius: '4px',
                fontSize: '0.75rem',
                color: colors.DARK_ORANGE
              }}>
                ⚠️ Fat tails detected
              </div>
            )}
            {marketData.skewness && marketData.skewness < -0.5 && (
              <div style={{ 
                padding: '0.25rem 0.5rem',
                backgroundColor: colors.LIGHT_RED,
                borderRadius: '4px',
                fontSize: '0.75rem',
                color: colors.DARK_RED
              }}>
                ⚠️ Negative skew
              </div>
            )}
          </div>
        </div>
      )}

      <div style={{ 
        marginTop: '1rem', 
        padding: '0.75rem',
        backgroundColor: colors.BLUE_98,
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: colors.DARK_GRAY
      }}>
        <strong>Note:</strong> Returns shown are nominal (not inflation-adjusted). 
        {marketData.calibration_method === 'GARCH-t' && ' Using GARCH model with fat-tailed distribution for improved forecasting.'}
        {marketData.calibration_method === 'Historical-Robust' && ' Using robust historical statistics with uncertainty quantification.'}
      </div>
    </div>
  )
}

export default MarketCalibration