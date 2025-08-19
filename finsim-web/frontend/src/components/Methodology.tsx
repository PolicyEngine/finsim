import React, { useState } from 'react'
import { colors } from '../styles/colors'

interface FAQItem {
  question: string
  answer: string | React.ReactElement
}

const Methodology: React.FC = () => {
  const [openItems, setOpenItems] = useState<Set<number>>(new Set())

  const toggleItem = (index: number) => {
    const newOpen = new Set(openItems)
    if (newOpen.has(index)) {
      newOpen.delete(index)
    } else {
      newOpen.add(index)
    }
    setOpenItems(newOpen)
  }

  const faqItems: FAQItem[] = [
    {
      question: "How do we forecast stock returns?",
      answer: (
        <div>
          <p>We use professional statistical models to forecast returns with proper uncertainty quantification:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li><strong>GARCH models</strong> when available - Industry standard for volatility forecasting that captures volatility clustering and fat tails</li>
            <li><strong>Historical CAGR</strong> as fallback - Compound Annual Growth Rate over the full history, more stable than arithmetic mean</li>
            <li><strong>Uncertainty bounds</strong> - We calculate standard errors based on sample size and volatility</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            All returns shown are nominal (not inflation-adjusted) to maintain consistency with how portfolios actually grow.
          </p>
        </div>
      )
    },
    {
      question: "Why do we see different results for different tickers?",
      answer: (
        <div>
          <p>Different index funds have different risk-return profiles based on their holdings:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li><strong>VT</strong> (Global stocks) - Most diversified, moderate returns and volatility</li>
            <li><strong>SPY/VOO</strong> (S&P 500) - US large-cap, historically higher returns but US-concentrated</li>
            <li><strong>QQQ</strong> (Nasdaq-100) - Tech-heavy, higher volatility and potential returns</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            Longer data history (SPY since 1993) provides more reliable estimates than newer funds (VT since 2008).
          </p>
        </div>
      )
    },
    {
      question: "How do we model mortality risk?",
      answer: (
        <div>
          <p>We use official Social Security Administration (SSA) actuarial tables:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>Gender-specific mortality rates by exact age</li>
            <li>Updated annually with latest population data</li>
            <li>Monte Carlo sampling - each simulation path has stochastic death timing</li>
            <li>Joint mortality for couples - both spouses modeled independently</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            This captures the real risk that you might not live to enjoy late-life wealth accumulation.
          </p>
        </div>
      )
    },
    {
      question: "How are taxes calculated?",
      answer: (
        <div>
          <p>We use PolicyEngine-US for accurate tax calculations:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li><strong>Federal taxes</strong> - Current tax brackets, standard deductions, capital gains rates</li>
            <li><strong>State taxes</strong> - Specific rules for your selected state</li>
            <li><strong>Social Security taxation</strong> - Provisional income thresholds</li>
            <li><strong>Capital gains</strong> - Long-term rates on investment withdrawals</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            This is far more accurate than simple rule-of-thumb tax estimates.
          </p>
        </div>
      )
    },
    {
      question: "What is Monte Carlo simulation?",
      answer: (
        <div>
          <p>Monte Carlo simulation runs thousands of possible future scenarios to understand the range of outcomes:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>Each simulation is one possible "life path" with random market returns and mortality</li>
            <li>Market returns are drawn from our calibrated distribution each year</li>
            <li>We track success rates (portfolio survives) and failure ages</li>
            <li>Percentiles (5th, 50th, 95th) show the range of likely outcomes</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            This captures sequence-of-returns risk - early losses hurt more than late losses in retirement.
          </p>
        </div>
      )
    },
    {
      question: "What does 'fat tails' warning mean?",
      answer: (
        <div>
          <p>Fat tails indicate that extreme events happen more often than a normal distribution would predict:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>Stock markets have more crashes and booms than bell curve suggests</li>
            <li>We detect this using <strong>excess kurtosis</strong> (values {'>'} 1 indicate fat tails)</li>
            <li>When detected, we use Student's t-distribution instead of normal</li>
            <li>This gives more realistic worst-case scenarios</li>
          </ul>
        </div>
      )
    },
    {
      question: "What does 'negative skew' warning mean?",
      answer: (
        <div>
          <p>Negative skew means crashes are larger than rallies:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>Markets tend to "take the stairs up and the elevator down"</li>
            <li>Large losses happen suddenly while gains accumulate slowly</li>
            <li>Skewness {'<'} -0.5 triggers our warning</li>
            <li>This asymmetry is important for retirement planning</li>
          </ul>
        </div>
      )
    },
    {
      question: "How do confidence intervals work?",
      answer: (
        <div>
          <p>When we show "7.0% ± 4.0%" for expected returns:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>7.0% is our best estimate (point forecast)</li>
            <li>± 4.0% is the 95% confidence interval</li>
            <li>True long-term return likely between 3.0% and 11.0%</li>
            <li>Wider intervals = more uncertainty (less data or higher volatility)</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            This parameter uncertainty feeds into our Monte Carlo simulations.
          </p>
        </div>
      )
    },
    {
      question: "Why use nominal instead of real returns?",
      answer: (
        <div>
          <p>We use nominal (not inflation-adjusted) returns throughout for consistency:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li>Your portfolio balance grows at nominal rates</li>
            <li>Social Security has built-in COLA adjustments</li>
            <li>Mixing real and nominal creates confusion</li>
            <li>You can adjust spending assumptions for expected inflation</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            Enter spending needs in today's dollars - the model handles growth appropriately.
          </p>
        </div>
      )
    },
    {
      question: "How accurate are these predictions?",
      answer: (
        <div>
          <p>Our predictions are as accurate as the underlying assumptions:</p>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
            <li><strong>Market returns</strong> - Based on historical data, but "past performance..."</li>
            <li><strong>Mortality</strong> - SSA tables are population averages, individual health varies</li>
            <li><strong>Taxes</strong> - Current law, but tax policy changes over time</li>
            <li><strong>Spending</strong> - You control this, but needs may change</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            Think of this as a framework for decision-making, not a crystal ball. The value is in understanding 
            the range of possible outcomes and key risk factors.
          </p>
        </div>
      )
    }
  ]

  return (
    <div className="pe-card">
      <h2 style={{ marginBottom: '1.5rem', color: colors.DARKEST_BLUE }}>
        Methodology & FAQ
      </h2>
      
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>
          How FinSim works
        </h3>
        <div style={{ 
          padding: '1rem',
          backgroundColor: colors.BLUE_98,
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          <p style={{ marginBottom: '0.75rem' }}>
            FinSim combines several sophisticated models to provide accurate retirement planning forecasts:
          </p>
          <ol style={{ marginLeft: '1.5rem', marginBottom: 0 }}>
            <li><strong>Market Calibration</strong> - Statistical analysis of historical returns with uncertainty quantification</li>
            <li><strong>Monte Carlo Simulation</strong> - Thousands of scenarios capturing market and mortality uncertainty</li>
            <li><strong>Tax Modeling</strong> - PolicyEngine's detailed federal and state tax calculations</li>
            <li><strong>Mortality Modeling</strong> - SSA actuarial tables with stochastic life expectancy</li>
          </ol>
        </div>
      </div>

      <div>
        <h3 style={{ color: colors.DARKEST_BLUE, marginBottom: '1rem' }}>
          Frequently asked questions
        </h3>
        
        {faqItems.map((item, index) => (
          <div 
            key={index}
            style={{ 
              marginBottom: '1rem',
              border: `1px solid ${colors.LIGHT_GRAY}`,
              borderRadius: '8px',
              overflow: 'hidden'
            }}
          >
            <button
              onClick={() => toggleItem(index)}
              style={{
                width: '100%',
                padding: '1rem',
                background: openItems.has(index) ? colors.BLUE_98 : colors.WHITE,
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '1rem',
                fontWeight: 500,
                color: colors.DARKEST_BLUE
              }}
            >
              <span>{item.question}</span>
              <span style={{ fontSize: '1.2rem', color: colors.TEAL_ACCENT }}>
                {openItems.has(index) ? '−' : '+'}
              </span>
            </button>
            
            {openItems.has(index) && (
              <div style={{ 
                padding: '1rem',
                backgroundColor: colors.WHITE,
                borderTop: `1px solid ${colors.LIGHT_GRAY}`,
                fontSize: '0.95rem',
                lineHeight: 1.6,
                color: colors.DARK_GRAY
              }}>
                {item.answer}
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ 
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: colors.TEAL_LIGHT,
        borderRadius: '8px',
        fontSize: '0.9rem'
      }}>
        <strong style={{ color: colors.TEAL_PRESSED }}>Pro tip:</strong>
        <p style={{ marginTop: '0.5rem', marginBottom: 0, color: colors.TEAL_PRESSED }}>
          Run simulations with different assumptions to understand sensitivity. 
          Small changes in returns or spending can have large impacts over 30+ year horizons.
          Focus on robust strategies that work across a range of scenarios rather than optimizing for one forecast.
        </p>
      </div>
    </div>
  )
}

export default Methodology