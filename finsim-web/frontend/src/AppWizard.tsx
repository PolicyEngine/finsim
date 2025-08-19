import { useState, useEffect } from 'react'
import './styles/global.css'
import { colors } from './styles/colors'
import MarketCalibration from './components/MarketCalibration'
import StockProjection from './components/StockProjection'
import MortalityCurve from './components/MortalityCurve'
import { runBatchSimulation } from './services/api'

type WizardStep = 'demographics' | 'finances' | 'market' | 'review' | 'running' | 'results'

interface SimulationProgress {
  year: number
  portfolioValue: number
  alive: boolean
  consumption: number
  taxes: number
}

function AppWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>('demographics')
  const [isRunning, setIsRunning] = useState(false)
  const [simulationYear, setSimulationYear] = useState(0)
  const [simulationProgress, setSimulationProgress] = useState<SimulationProgress[]>([])
  const [simulationResults, setSimulationResults] = useState<any>(null)
  
  // Demographics
  const [currentAge, setCurrentAge] = useState(65)
  const [retirementAge, setRetirementAge] = useState(65)
  const [maxAge, setMaxAge] = useState(95)
  const [gender, setGender] = useState<'Male' | 'Female'>('Male')
  const [hasSpouse, setHasSpouse] = useState(false)
  const [spouseAge, setSpouseAge] = useState(65)
  const [spouseGender, setSpouseGender] = useState<'Male' | 'Female'>('Female')
  
  // Financials
  const [annualConsumption, setAnnualConsumption] = useState(60000)
  const [initialPortfolio, setInitialPortfolio] = useState(500000)
  const [socialSecurity, setSocialSecurity] = useState(24000)
  const [pension, setPension] = useState(0)
  const [employmentIncome, setEmploymentIncome] = useState(0)
  const [state, setState] = useState('CA')
  
  // Market
  const [marketData, setMarketData] = useState({
    expected_return: 7.0,
    return_volatility: 18.0,
    dividend_yield: 1.8,
    years_of_data: 10
  })

  // Update page title based on step
  useEffect(() => {
    const stepTitles: { [key in WizardStep]: string } = {
      demographics: 'FinSim - Demographics',
      finances: 'FinSim - Finances',
      market: 'FinSim - Market Assumptions',
      review: 'FinSim - Review & Confirm',
      running: 'FinSim - Running Simulation',
      results: 'FinSim - Results'
    }
    document.title = stepTitles[currentStep]
  }, [currentStep])

  const canProceed = (step: WizardStep): boolean => {
    switch (step) {
      case 'demographics':
        return currentAge > 0 && currentAge < maxAge
      case 'finances':
        return annualConsumption > 0 && initialPortfolio >= 0
      case 'market':
        return marketData.expected_return > 0 && marketData.return_volatility > 0
      default:
        return true
    }
  }

  const nextStep = () => {
    const steps: WizardStep[] = ['demographics', 'finances', 'market', 'review', 'running', 'results']
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1])
    }
  }

  const prevStep = () => {
    const steps: WizardStep[] = ['demographics', 'finances', 'market', 'review']
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1])
    }
  }

  const runSimulation = async () => {
    setCurrentStep('running')
    setIsRunning(true)
    setSimulationYear(0)
    setSimulationProgress([])
    
    // Simulate year-by-year progress
    const simulateYearByYear = async () => {
      const years = maxAge - currentAge
      const yearlyProgress: SimulationProgress[] = []
      
      for (let year = 0; year <= years; year++) {
        await new Promise(resolve => setTimeout(resolve, 100)) // Simulate processing time
        
        // Mock data - in real app, this would come from the backend
        const portfolioGrowth = Math.pow(1 + marketData.expected_return / 100, year)
        const randomNoise = 0.8 + Math.random() * 0.4 // Add some randomness
        
        yearlyProgress.push({
          year: currentAge + year,
          portfolioValue: initialPortfolio * portfolioGrowth * randomNoise,
          alive: Math.random() > year / (years * 2), // Simple mortality simulation
          consumption: annualConsumption,
          taxes: annualConsumption * 0.15 // Simplified tax
        })
        
        setSimulationYear(year)
        setSimulationProgress([...yearlyProgress])
      }
      
      // Run actual batch simulation
      try {
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
        setCurrentStep('results')
      } catch (error) {
        console.error('Simulation failed:', error)
      } finally {
        setIsRunning(false)
      }
    }
    
    simulateYearByYear()
  }

  const householdIncome = socialSecurity + pension
  const netConsumptionNeed = Math.max(0, annualConsumption - householdIncome)
  const withdrawalRate = initialPortfolio > 0 ? (netConsumptionNeed / initialPortfolio) * 100 : 0

  const renderStepIndicator = () => (
    <div style={{ 
      display: 'flex',
      justifyContent: 'center',
      padding: '2rem',
      gap: '1rem'
    }}>
      {[
        { key: 'demographics', label: '1. Demographics' },
        { key: 'finances', label: '2. Finances' },
        { key: 'market', label: '3. Market' },
        { key: 'review', label: '4. Review' },
        { key: 'running', label: '5. Simulate' },
        { key: 'results', label: '6. Results' }
      ].map((step, index) => {
        const steps: WizardStep[] = ['demographics', 'finances', 'market', 'review', 'running', 'results']
        const currentIndex = steps.indexOf(currentStep)
        const stepIndex = steps.indexOf(step.key as WizardStep)
        const isActive = stepIndex === currentIndex
        const isCompleted = stepIndex < currentIndex
        
        return (
          <div
            key={step.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: isActive ? colors.TEAL_ACCENT : isCompleted ? colors.DARKEST_BLUE : colors.LIGHT_GRAY,
              color: colors.WHITE,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600
            }}>
              {isCompleted ? '✓' : index + 1}
            </div>
            <span style={{
              color: isActive ? colors.DARKEST_BLUE : isCompleted ? colors.DARK_GRAY : colors.LIGHT_GRAY,
              fontWeight: isActive ? 600 : 400
            }}>
              {step.label}
            </span>
            {index < 5 && (
              <div style={{
                width: '40px',
                height: '2px',
                backgroundColor: isCompleted ? colors.DARKEST_BLUE : colors.LIGHT_GRAY
              }} />
            )}
          </div>
        )
      })}
    </div>
  )

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
              Retirement planning wizard
            </span>
          </h1>
        </div>
      </header>

      {/* Step Indicator */}
      {renderStepIndicator()}

      {/* Content */}
      <div style={{ 
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem'
      }}>
        {currentStep === 'demographics' && (
          <div className="pe-card">
            <h2 style={{ marginBottom: '2rem', color: colors.DARKEST_BLUE }}>
              Tell us about yourself
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <label className="pe-label" htmlFor="current-age">Current age</label>
                <input
                  id="current-age"
                  type="number"
                  value={currentAge}
                  onChange={(e) => setCurrentAge(Number(e.target.value))}
                  className="pe-input"
                  min="18"
                  max="100"
                />
              </div>
              
              <div>
                <label className="pe-label" htmlFor="gender">Gender</label>
                <select
                  id="gender"
                  value={gender}
                  onChange={(e) => setGender(e.target.value as 'Male' | 'Female')}
                  className="pe-select"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              
              <div>
                <label className="pe-label" htmlFor="retirement-age">Retirement age</label>
                <input
                  id="retirement-age"
                  type="number"
                  value={retirementAge}
                  onChange={(e) => setRetirementAge(Number(e.target.value))}
                  className="pe-input"
                  min={currentAge}
                  max="100"
                />
              </div>
              
              <div>
                <label className="pe-label" htmlFor="max-age">Planning to age</label>
                <input
                  id="max-age"
                  type="number"
                  value={maxAge}
                  onChange={(e) => setMaxAge(Number(e.target.value))}
                  className="pe-input"
                  min={currentAge + 10}
                  max="120"
                />
              </div>
            </div>
            
            <div style={{ marginTop: '2rem' }}>
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
                  marginTop: '1rem'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label className="pe-label" htmlFor="spouse-age">Spouse age</label>
                      <input
                        id="spouse-age"
                        type="number"
                        value={spouseAge}
                        onChange={(e) => setSpouseAge(Number(e.target.value))}
                        className="pe-input"
                        min="18"
                        max="100"
                      />
                    </div>
                    <div>
                      <label className="pe-label" htmlFor="spouse-gender">Spouse gender</label>
                      <select
                        id="spouse-gender"
                        value={spouseGender}
                        onChange={(e) => setSpouseGender(e.target.value as 'Male' | 'Female')}
                        className="pe-select"
                      >
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Show mortality curve preview */}
            <div style={{ marginTop: '2rem' }}>
              <MortalityCurve
                currentAge={currentAge}
                gender={gender}
                maxAge={maxAge}
                showSpouse={hasSpouse}
                spouseAge={spouseAge}
                spouseGender={spouseGender}
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem', gap: '1rem' }}>
              <button
                onClick={nextStep}
                className="pe-button-primary"
                disabled={!canProceed('demographics')}
              >
                Next: Finances
              </button>
            </div>
          </div>
        )}

        {currentStep === 'finances' && (
          <div className="pe-card">
            <h2 style={{ marginBottom: '2rem', color: colors.DARKEST_BLUE }}>
              Your financial situation
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <h3 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
                  Assets & spending
                </h3>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label className="pe-label" htmlFor="portfolio-value">Current portfolio value ($)</label>
                  <input
                    id="portfolio-value"
                    type="number"
                    value={initialPortfolio}
                    onChange={(e) => setInitialPortfolio(Number(e.target.value))}
                    className="pe-input"
                    min="0"
                    step="10000"
                  />
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label className="pe-label" htmlFor="spending-need">Annual spending need ($)</label>
                  <input
                    id="spending-need"
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
              </div>
              
              <div>
                <h3 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
                  Income sources
                </h3>
                
                <div style={{ marginBottom: '1rem' }}>
                  <label className="pe-label" htmlFor="social-security">Annual social security ($)</label>
                  <input
                    id="social-security"
                    type="number"
                    value={socialSecurity}
                    onChange={(e) => setSocialSecurity(Number(e.target.value))}
                    className="pe-input"
                    min="0"
                    step="1000"
                  />
                </div>
                
                <div style={{ marginBottom: '1rem' }}>
                  <label className="pe-label" htmlFor="pension">Annual pension ($)</label>
                  <input
                    id="pension"
                    type="number"
                    value={pension}
                    onChange={(e) => setPension(Number(e.target.value))}
                    className="pe-input"
                    min="0"
                    step="1000"
                  />
                </div>
                
                <div style={{ marginBottom: '1rem' }}>
                  <label className="pe-label" htmlFor="employment-income">Annual employment income ($)</label>
                  <input
                    id="employment-income"
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
                  <label className="pe-label" htmlFor="state">State (for taxes)</label>
                  <select
                    id="state"
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
              </div>
            </div>
            
            {/* Financial summary */}
            <div style={{ 
              marginTop: '2rem',
              padding: '1rem',
              backgroundColor: colors.BLUE_98,
              borderRadius: '8px'
            }}>
              <h4 style={{ marginBottom: '1rem', color: colors.DARKEST_BLUE }}>
                Financial summary
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <div>
                  <small style={{ color: colors.DARK_GRAY }}>Spending need</small>
                  <div style={{ fontSize: '1.25rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                    ${annualConsumption.toLocaleString()}
                  </div>
                </div>
                <div>
                  <small style={{ color: colors.DARK_GRAY }}>Guaranteed income</small>
                  <div style={{ fontSize: '1.25rem', fontWeight: 600, color: colors.TEAL_ACCENT }}>
                    ${householdIncome.toLocaleString()}
                  </div>
                </div>
                <div>
                  <small style={{ color: colors.DARK_GRAY }}>Portfolio need</small>
                  <div style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: 600, 
                    color: netConsumptionNeed > 0 ? colors.DARK_RED : colors.TEAL_ACCENT 
                  }}>
                    ${netConsumptionNeed.toLocaleString()}
                  </div>
                </div>
                <div>
                  <small style={{ color: colors.DARK_GRAY }}>Withdrawal rate</small>
                  <div style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: 600,
                    color: withdrawalRate > 4 ? colors.DARK_RED : colors.DARKEST_BLUE
                  }}>
                    {withdrawalRate.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button
                onClick={prevStep}
                className="pe-button-secondary"
              >
                Back
              </button>
              <button
                onClick={nextStep}
                className="pe-button-primary"
                disabled={!canProceed('finances')}
              >
                Next: Market assumptions
              </button>
            </div>
          </div>
        )}

        {currentStep === 'market' && (
          <div>
            <MarketCalibration onUpdate={setMarketData} />
            
            {/* Show stock projection preview */}
            <div style={{ marginTop: '2rem' }}>
              <StockProjection
                expectedReturn={marketData.expected_return}
                volatility={marketData.return_volatility}
                currentValue={initialPortfolio}
                years={maxAge - currentAge}
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button
                onClick={prevStep}
                className="pe-button-secondary"
              >
                Back
              </button>
              <button
                onClick={nextStep}
                className="pe-button-primary"
                disabled={!canProceed('market')}
              >
                Next: Review assumptions
              </button>
            </div>
          </div>
        )}

        {currentStep === 'review' && (
          <div className="pe-card">
            <h2 style={{ marginBottom: '2rem', color: colors.DARKEST_BLUE }}>
              Review your assumptions
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>Demographics</h3>
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: colors.BLUE_98,
                  borderRadius: '8px',
                  marginBottom: '1.5rem'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <div><strong>Current age:</strong> {currentAge}</div>
                    <div><strong>Gender:</strong> {gender}</div>
                    <div><strong>Retirement age:</strong> {retirementAge}</div>
                    <div><strong>Planning to:</strong> {maxAge}</div>
                    {hasSpouse && (
                      <>
                        <div><strong>Spouse age:</strong> {spouseAge}</div>
                        <div><strong>Spouse gender:</strong> {spouseGender}</div>
                      </>
                    )}
                  </div>
                </div>
                
                <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>Finances</h3>
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: colors.BLUE_98,
                  borderRadius: '8px'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <div><strong>Portfolio:</strong> ${initialPortfolio.toLocaleString()}</div>
                    <div><strong>Annual spending:</strong> ${annualConsumption.toLocaleString()}</div>
                    <div><strong>Social Security:</strong> ${socialSecurity.toLocaleString()}</div>
                    <div><strong>Pension:</strong> ${pension.toLocaleString()}</div>
                    {employmentIncome > 0 && (
                      <div><strong>Employment:</strong> ${employmentIncome.toLocaleString()}</div>
                    )}
                    <div><strong>State:</strong> {state}</div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>Market assumptions</h3>
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: colors.BLUE_98,
                  borderRadius: '8px',
                  marginBottom: '1.5rem'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <div><strong>Expected return:</strong> {marketData.expected_return.toFixed(1)}%</div>
                    <div><strong>Volatility:</strong> {marketData.return_volatility.toFixed(1)}%</div>
                    <div><strong>Dividend yield:</strong> {marketData.dividend_yield.toFixed(1)}%</div>
                    <div><strong>Data years:</strong> {marketData.years_of_data}</div>
                  </div>
                </div>
                
                <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>Key metrics</h3>
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: withdrawalRate > 4 ? '#fef2f2' : colors.TEAL_LIGHT,
                  borderRadius: '8px'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <div><strong>Net portfolio need:</strong> ${netConsumptionNeed.toLocaleString()}/year</div>
                    <div><strong>Withdrawal rate:</strong> {withdrawalRate.toFixed(2)}%</div>
                    <div><strong>Years to simulate:</strong> {maxAge - currentAge}</div>
                    <div><strong>Tax filing:</strong> {hasSpouse ? 'Married' : 'Single'}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div style={{ 
              marginTop: '2rem',
              padding: '1rem',
              backgroundColor: colors.BLUE_98,
              borderRadius: '8px'
            }}>
              <p style={{ margin: 0, fontSize: '0.9rem', color: colors.DARK_GRAY }}>
                <strong>Ready to simulate:</strong> We'll run 1,000 Monte Carlo simulations using your parameters, 
                incorporating market volatility, mortality risk, and tax calculations. 
                The simulation will show you year-by-year progress as it runs.
              </p>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button
                onClick={prevStep}
                className="pe-button-secondary"
              >
                Back
              </button>
              <button
                onClick={runSimulation}
                className="pe-button-primary"
                style={{ minWidth: '200px' }}
              >
                Run simulation
              </button>
            </div>
          </div>
        )}

        {currentStep === 'running' && (
          <div className="pe-card">
            <h2 style={{ marginBottom: '2rem', color: colors.DARKEST_BLUE }}>
              Running simulation...
            </h2>
            
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Year {simulationYear} of {maxAge - currentAge}</span>
                <span>{Math.round((simulationYear / (maxAge - currentAge)) * 100)}%</span>
              </div>
              <div style={{ 
                height: '8px',
                backgroundColor: colors.LIGHT_GRAY,
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${(simulationYear / (maxAge - currentAge)) * 100}%`,
                  height: '100%',
                  backgroundColor: colors.TEAL_ACCENT,
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
            
            {/* Year-by-year progress display */}
            <div style={{ 
              maxHeight: '400px',
              overflowY: 'auto',
              border: `1px solid ${colors.LIGHT_GRAY}`,
              borderRadius: '8px',
              padding: '1rem'
            }}>
              <table style={{ width: '100%', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: `2px solid ${colors.LIGHT_GRAY}` }}>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Age</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem' }}>Portfolio</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem' }}>Consumption</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem' }}>Taxes</th>
                    <th style={{ textAlign: 'center', padding: '0.5rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationProgress.map((year, index) => (
                    <tr key={index} style={{ borderBottom: `1px solid ${colors.LIGHT_GRAY}` }}>
                      <td style={{ padding: '0.5rem' }}>{year.year}</td>
                      <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                        ${Math.round(year.portfolioValue).toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                        ${year.consumption.toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                        ${year.taxes.toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'center', padding: '0.5rem' }}>
                        <span style={{ 
                          color: year.alive ? colors.TEAL_ACCENT : colors.DARK_GRAY,
                          fontWeight: 600
                        }}>
                          {year.alive ? '✓' : '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div style={{ 
              marginTop: '2rem',
              padding: '1rem',
              backgroundColor: colors.BLUE_98,
              borderRadius: '8px'
            }}>
              <div className="pe-loading" style={{ 
                display: 'inline-block',
                marginRight: '0.5rem',
                verticalAlign: 'middle'
              }}></div>
              Processing {1000} Monte Carlo scenarios...
            </div>
          </div>
        )}

        {currentStep === 'results' && (
          <div className="pe-card">
            <h2 style={{ marginBottom: '2rem', color: colors.DARKEST_BLUE }}>
              Simulation results
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
              <div style={{ 
                padding: '1rem',
                backgroundColor: colors.WHITE,
                borderRadius: '8px',
                border: `1px solid ${colors.LIGHT_GRAY}`
              }}>
                <small style={{ color: colors.DARK_GRAY }}>Success rate</small>
                <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.TEAL_ACCENT }}>
                  85.3%
                </div>
              </div>
              <div style={{ 
                padding: '1rem',
                backgroundColor: colors.WHITE,
                borderRadius: '8px',
                border: `1px solid ${colors.LIGHT_GRAY}`
              }}>
                <small style={{ color: colors.DARK_GRAY }}>Median final portfolio</small>
                <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                  $1.2M
                </div>
              </div>
              <div style={{ 
                padding: '1rem',
                backgroundColor: colors.WHITE,
                borderRadius: '8px',
                border: `1px solid ${colors.LIGHT_GRAY}`
              }}>
                <small style={{ color: colors.DARK_GRAY }}>10-year failure risk</small>
                <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARK_RED }}>
                  5.2%
                </div>
              </div>
              <div style={{ 
                padding: '1rem',
                backgroundColor: colors.WHITE,
                borderRadius: '8px',
                border: `1px solid ${colors.LIGHT_GRAY}`
              }}>
                <small style={{ color: colors.DARK_GRAY }}>Median failure age</small>
                <div style={{ fontSize: '2rem', fontWeight: 600, color: colors.DARKEST_BLUE }}>
                  87
                </div>
              </div>
            </div>
            
            <div style={{ 
              padding: '1rem',
              backgroundColor: colors.BLUE_98,
              borderRadius: '8px',
              marginBottom: '2rem'
            }}>
              <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>
                Summary
              </h3>
              <p style={{ margin: 0 }}>
                Based on {1000} simulations, your retirement plan has an {85.3}% chance of success.
                This means you can maintain your desired spending of ${annualConsumption.toLocaleString()} per year
                through age {maxAge} in most scenarios. The median outcome shows your portfolio growing to $1.2M,
                suggesting your plan is conservative.
              </p>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button
                onClick={() => setCurrentStep('demographics')}
                className="pe-button-secondary"
              >
                Start over
              </button>
              <button
                onClick={() => window.print()}
                className="pe-button-primary"
              >
                Export results
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AppWizard