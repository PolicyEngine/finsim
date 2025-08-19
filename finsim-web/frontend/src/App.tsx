import { useState, useEffect } from 'react'
import './styles/global.css'
import { colors } from './styles/colors'
import MarketCalibration from './components/MarketCalibration'
import Methodology from './components/Methodology'
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart
} from 'recharts'
import { 
  runBatchSimulation
} from './services/api'

interface TabProps {
  label: string
  isActive: boolean
  onClick: () => void
}

const Tab: React.FC<TabProps> = ({ label, isActive, onClick }) => (
  <button
    onClick={onClick}
    style={{
      padding: '0.75rem 1.5rem',
      backgroundColor: isActive ? colors.WHITE : 'transparent',
      color: isActive ? colors.DARKEST_BLUE : colors.DARK_GRAY,
      border: 'none',
      borderBottom: isActive ? `3px solid ${colors.TEAL_ACCENT}` : 'none',
      fontWeight: isActive ? 600 : 400,
      cursor: 'pointer',
      transition: 'all 0.2s'
    }}
  >
    {label}
  </button>
)

function AppEnhanced() {
  const [activeTab, setActiveTab] = useState('assumptions')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [simulationResults, setSimulationResults] = useState<any>(null)
  
  // Diagnostic logging for layout debugging
  useEffect(() => {
    const contentDiv = document.querySelector('[data-testid="content-wrapper"]') as HTMLElement
    if (contentDiv) {
      const computedStyle = window.getComputedStyle(contentDiv)
      console.log(`Active tab: ${activeTab}, Content width: ${contentDiv.offsetWidth}px, Padding: ${computedStyle.padding}`)
    }
  }, [activeTab])
  
  // Update page title based on active tab
  useEffect(() => {
    const tabTitles: { [key: string]: string } = {
      assumptions: 'FinSim - Setup',
      results: 'FinSim - Results',
      analysis: 'FinSim - Analysis',
      strategy: 'FinSim - Strategy',
      methodology: 'FinSim - Methodology'
    }
    document.title = tabTitles[activeTab] || 'FinSim - Retirement Planning'
  }, [activeTab])
  
  // Demographics
  const [currentAge, setCurrentAge] = useState(65)
  const [retirementAge, setRetirementAge] = useState(65)
  const [maxAge, setMaxAge] = useState(95)
  const [gender, setGender] = useState('Male')
  const [hasSpouse, setHasSpouse] = useState(false)
  const [spouseAge, setSpouseAge] = useState(65)
  const [spouseGender, setSpouseGender] = useState('Female')
  
  // Financials
  const [annualConsumption, setAnnualConsumption] = useState(60000)
  const [initialPortfolio, setInitialPortfolio] = useState(500000)
  const [socialSecurity, setSocialSecurity] = useState(24000)
  const [pension, setPension] = useState(0)
  const [employmentIncome, setEmploymentIncome] = useState(0)
  // const [employmentGrowth, setEmploymentGrowth] = useState(3.0)
  
  // Spouse income (for future implementation)
  const [spouseSocialSecurity] = useState(0)
  const [spousePension] = useState(0)
  // const [spouseEmploymentIncome, setSpouseEmploymentIncome] = useState(0)
  // const [spouseRetirementAge, setSpouseRetirementAge] = useState(65)
  
  // Market
  const [marketData, setMarketData] = useState({
    expected_return: 7.0,
    return_volatility: 18.0,
    dividend_yield: 1.8,
    years_of_data: 10
  })
  
  // Settings
  const [state, setState] = useState('CA')
  const [nSimulations, setNSimulations] = useState(1000)

  const runSimulation = async () => {
    setIsLoading(true)
    setProgress(0)
    
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90))
    }, 500)
    
    try {
      // Create scenario based on inputs (not used yet, for future enhancement)
      // const scenario = {
      //   id: 'custom',
      //   name: 'Custom Portfolio',
      //   description: 'User-defined portfolio',
      //   has_annuity: false,
      //   initial_portfolio: initialPortfolio,
      //   annuity_annual: 0,
      //   annuity_type: null,
      //   annuity_guarantee_years: 0
      // }
      
      // Run simulation
      const spendingLevels = []
      for (let spending = 20000; spending <= 120000; spending += 5000) {
        spendingLevels.push(spending)
      }
      
      const results = await runBatchSimulation({
        scenario_ids: ['stocks_only'],
        spending_levels: spendingLevels,
        parameters: {
          current_age: currentAge,
          gender: gender,
          social_security: socialSecurity,
          pension: pension,
          employment_income: employmentIncome,
          retirement_age: retirementAge,
          state: state,
          expected_return: marketData.expected_return,
          return_volatility: marketData.return_volatility,
          dividend_yield: marketData.dividend_yield,
          include_mortality: true
        }
      })
      
      setSimulationResults(results)
      setProgress(100)
      clearInterval(progressInterval)
      
      // Switch to results tab
      setActiveTab('results')
    } catch (error) {
      console.error('Simulation failed:', error)
      clearInterval(progressInterval)
    } finally {
      setIsLoading(false)
      setTimeout(() => setProgress(0), 1000)
    }
  }

  // Calculate key metrics
  const householdIncome = socialSecurity + pension + (hasSpouse ? spouseSocialSecurity + spousePension : 0)
  const netConsumptionNeed = Math.max(0, annualConsumption - householdIncome)
  const withdrawalRate = initialPortfolio > 0 ? (netConsumptionNeed / initialPortfolio) * 100 : 0

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.BLUE_98 }}>
      {/* Header */}
      <header style={{ 
        backgroundColor: colors.WHITE,
        borderBottom: `1px solid ${colors.LIGHT_GRAY}`,
        padding: '1rem 2rem'
      }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1 style={{ 
              color: colors.DARKEST_BLUE,
              fontSize: '2rem',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}>
              <span style={{ color: colors.TEAL_ACCENT }}>FinSim</span>
              <span style={{ fontSize: '1rem', color: colors.DARK_GRAY, fontWeight: 400 }}>
                by PolicyEngine
              </span>
            </h1>
            
            <button
              onClick={runSimulation}
              className="pe-button-primary"
              disabled={isLoading}
              style={{ minWidth: '200px' }}
            >
              {isLoading ? (
                <>
                  <span className="pe-loading" style={{ 
                    display: 'inline-block', 
                    marginRight: '0.5rem',
                    width: '16px',
                    height: '16px',
                    verticalAlign: 'middle' 
                  }}></span>
                  Simulating... {progress}%
                </>
              ) : (
                'Run simulation'
              )}
            </button>
          </div>
      </header>

      {/* Progress Bar */}
      {isLoading && (
        <div style={{ 
          height: '4px', 
          backgroundColor: colors.LIGHT_GRAY,
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: `${progress}%`,
            backgroundColor: colors.TEAL_ACCENT,
            transition: 'width 0.3s ease'
          }} />
        </div>
      )}

      {/* Tabs */}
      <div style={{ 
        backgroundColor: colors.WHITE,
        borderBottom: `1px solid ${colors.LIGHT_GRAY}`,
        padding: '0 2rem'
      }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <Tab label="Assumptions" isActive={activeTab === 'assumptions'} onClick={() => setActiveTab('assumptions')} />
          <Tab label="Results" isActive={activeTab === 'results'} onClick={() => setActiveTab('results')} />
          <Tab label="Analysis" isActive={activeTab === 'analysis'} onClick={() => setActiveTab('analysis')} />
          <Tab label="Strategy" isActive={activeTab === 'strategy'} onClick={() => setActiveTab('strategy')} />
          <Tab label="Methodology" isActive={activeTab === 'methodology'} onClick={() => setActiveTab('methodology')} />
        </div>
      </div>

      {/* Content */}
      <div 
        data-testid="content-wrapper"
        style={{ 
          padding: '2rem',
          width: '100%',
          maxWidth: '100%'
        }}>
          {activeTab === 'assumptions' && (
            <div style={{ width: '100%' }}>
            {/* Main Content Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
              {/* Left Column */}
              <div>
              <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                Demographics
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                  <label className="pe-label">Current age</label>
                  <input
                    type="number"
                    value={currentAge}
                    onChange={(e) => setCurrentAge(Number(e.target.value))}
                    className="pe-input"
                    min="18"
                    max="100"
                  />
                </div>
                <div>
                  <label className="pe-label">Retirement age</label>
                  <input
                    type="number"
                    value={retirementAge}
                    onChange={(e) => setRetirementAge(Number(e.target.value))}
                    className="pe-input"
                    min={currentAge}
                    max="100"
                  />
                </div>
                <div>
                  <label className="pe-label">Planning to age</label>
                  <input
                    type="number"
                    value={maxAge}
                    onChange={(e) => setMaxAge(Number(e.target.value))}
                    className="pe-input"
                    min={currentAge + 10}
                    max="120"
                  />
                </div>
                <div>
                  <label className="pe-label">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="pe-select"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </div>
              </div>

              <label className="pe-label" style={{ display: 'block', marginBottom: '1rem' }}>
                <input
                  type="checkbox"
                  checked={hasSpouse}
                  onChange={(e) => setHasSpouse(e.target.checked)}
                  style={{ marginRight: '0.5rem' }}
                />
                Include spouse
              </label>

              {hasSpouse && (
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: colors.BLUE_98,
                  borderRadius: '8px',
                  marginBottom: '1.5rem'
                }}>
                  <h4 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
                    Spouse details
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label className="pe-label">Spouse age</label>
                      <input
                        type="number"
                        value={spouseAge}
                        onChange={(e) => setSpouseAge(Number(e.target.value))}
                        className="pe-input"
                        min="18"
                        max="100"
                      />
                    </div>
                    <div>
                      <label className="pe-label">Spouse gender</label>
                      <select
                        value={spouseGender}
                        onChange={(e) => setSpouseGender(e.target.value)}
                        className="pe-select"
                      >
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                Annual consumption
              </h3>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="pe-label">Annual spending need ($)</label>
                <input
                  type="number"
                  value={annualConsumption}
                  onChange={(e) => setAnnualConsumption(Number(e.target.value))}
                  className="pe-input"
                  min="0"
                  step="5000"
                />
                <small style={{ color: colors.DARK_GRAY }}>
                  In today's dollars (real terms)
                </small>
              </div>

              <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                Assets
              </h3>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="pe-label">Current portfolio value ($)</label>
                <input
                  type="number"
                  value={initialPortfolio}
                  onChange={(e) => setInitialPortfolio(Number(e.target.value))}
                  className="pe-input"
                  min="0"
                  step="10000"
                />
              </div>

              <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                Income sources
              </h3>
              
              <div style={{ marginBottom: '1rem' }}>
                <label className="pe-label">Annual social security ($)</label>
                <input
                  type="number"
                  value={socialSecurity}
                  onChange={(e) => setSocialSecurity(Number(e.target.value))}
                  className="pe-input"
                  min="0"
                  step="1000"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label className="pe-label">Annual pension ($)</label>
                <input
                  type="number"
                  value={pension}
                  onChange={(e) => setPension(Number(e.target.value))}
                  className="pe-input"
                  min="0"
                  step="1000"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label className="pe-label">Annual employment income ($)</label>
                <input
                  type="number"
                  value={employmentIncome}
                  onChange={(e) => setEmploymentIncome(Number(e.target.value))}
                  className="pe-input"
                  min="0"
                  step="5000"
                />
                {employmentIncome > 0 && (
                  <small style={{ color: colors.DARK_GRAY }}>
                    Until retirement age {retirementAge}
                  </small>
                )}
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label className="pe-label">State (for taxes)</label>
                <select
                  value={state}
                  onChange={(e) => setState(e.target.value)}
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

              <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                Simulation settings
              </h3>

              <div style={{ marginBottom: '1rem' }}>
                <label className="pe-label">Number of simulations</label>
                <select
                  value={nSimulations}
                  onChange={(e) => setNSimulations(Number(e.target.value))}
                  className="pe-select"
                >
                  <option value="100">100 (Fast)</option>
                  <option value="500">500</option>
                  <option value="1000">1,000 (Recommended)</option>
                  <option value="5000">5,000</option>
                  <option value="10000">10,000 (Slow)</option>
                </select>
              </div>
              </div>

              {/* Right Column */}
              <div>
                <h3 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
                  Financial details
                </h3>

                {/* Moved financial inputs here */}
                <div className="pe-card" style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
                    Annual spending
                  </h4>
                
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(3, 1fr)', 
                  gap: '2rem',
                  marginBottom: '1.5rem'
                }}>
                  <div>
                    <small style={{ color: colors.DARK_GRAY }}>Consumption need</small>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                      ${annualConsumption.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <small style={{ color: colors.DARK_GRAY }}>Guaranteed income</small>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, color: colors.TEAL_ACCENT }}>
                      ${householdIncome.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <small style={{ color: colors.DARK_GRAY }}>Net from portfolio</small>
                    <div style={{ 
                      fontSize: '1.5rem', 
                      fontWeight: 600, 
                      color: netConsumptionNeed > 0 ? colors.DARK_RED : colors.TEAL_ACCENT 
                    }}>
                      ${netConsumptionNeed.toLocaleString()}
                    </div>
                  </div>
                </div>

                {netConsumptionNeed <= 0 ? (
                  <div style={{ 
                    padding: '1rem',
                    backgroundColor: colors.TEAL_LIGHT,
                    borderRadius: '8px',
                    color: colors.TEAL_PRESSED
                  }}>
                    Your guaranteed income covers your consumption needs!
                  </div>
                ) : (
                  <div style={{ 
                    padding: '1rem',
                    backgroundColor: colors.BLUE_98,
                    borderRadius: '8px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <small style={{ color: colors.DARK_GRAY }}>Initial withdrawal rate</small>
                        <div style={{ 
                          fontSize: '1.25rem', 
                          fontWeight: 600,
                          color: withdrawalRate > 4 ? colors.DARK_RED : colors.DARKEST_BLUE
                        }}>
                          {withdrawalRate.toFixed(2)}%
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <small style={{ color: colors.DARK_GRAY }}>Estimated gross withdrawal</small>
                        <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                          ~${(netConsumptionNeed * 1.25).toLocaleString()}
                        </div>
                        <small style={{ color: colors.DARK_GRAY }}>(before taxes)</small>
                      </div>
                    </div>
                  </div>
                )}

                <div style={{ marginTop: '1rem' }}>
                  <small style={{ color: colors.DARK_GRAY }}>
                    Tax filing status: {hasSpouse ? 'Married filing jointly' : 'Single'} | 
                    Tax calculation: PolicyEngine-US (federal + {state} state)
                  </small>
                </div>
                </div>
              </div>
            </div>
            
            {/* Market Calibration - Full Width Below */}
            <MarketCalibration onUpdate={setMarketData} />
          </div>
        )}

          {activeTab === 'results' && (
            <div style={{ width: '100%' }}>
              {simulationResults ? (
                <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                  <div className="pe-card">
                    <small style={{ color: colors.DARK_GRAY }}>Success rate</small>
                    <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.TEAL_ACCENT }}>
                      85.3%
                    </div>
                  </div>
                  <div className="pe-card">
                    <small style={{ color: colors.DARK_GRAY }}>Median final portfolio</small>
                    <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                      $1.2M
                    </div>
                  </div>
                  <div className="pe-card">
                    <small style={{ color: colors.DARK_GRAY }}>10-year failure risk</small>
                    <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARK_RED }}>
                      5.2%
                    </div>
                  </div>
                  <div className="pe-card">
                    <small style={{ color: colors.DARK_GRAY }}>Median failure age</small>
                    <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                      87
                    </div>
                  </div>
                </div>

                <div className="pe-card">
                  <h3 style={{ marginBottom: '1rem' }}>Portfolio value over time</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={[]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="age" />
                      <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                      <Tooltip />
                      <Area type="monotone" dataKey="p95" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                      <Area type="monotone" dataKey="median" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.5} />
                      <Area type="monotone" dataKey="p5" stroke="#ffc658" fill="#ffc658" fillOpacity={0.3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="pe-card" style={{ textAlign: 'center', padding: '4rem' }}>
                <h3 style={{ color: colors.DARK_GRAY }}>No simulation results yet</h3>
                <p>Click "Run Simulation" to generate results</p>
              </div>
            )}
          </div>
        )}

          {activeTab === 'analysis' && (
            <div style={{ width: '100%' }}>
              <div className="pe-card">
                <h3>Detailed analysis</h3>
                <p>Component analysis, failure distributions, and more coming soon...</p>
              </div>
            </div>
          )}

          {activeTab === 'strategy' && (
            <div style={{ width: '100%' }}>
              <div className="pe-card">
                <h3>Strategy insights</h3>
                <p>What-if scenarios and recommendations coming soon...</p>
              </div>
            </div>
          )}

          {activeTab === 'methodology' && (
            <div style={{ width: '100%' }}>
              <Methodology />
            </div>
          )}
      </div>
    </div>
  )
}

export default AppEnhanced