# FinSim Issues and Enhancements

## Enhancement: Make Dividend Yield Stochastic

**Current Behavior:**
- Dividend yield is modeled as a fixed percentage of portfolio value
- This assumes constant dividend yield over time

**Proposed Enhancement:**
- Model dividend yield as a stochastic process
- Options to consider:
  1. Mean-reverting process (Ornstein-Uhlenbeck)
  2. Correlated with market returns (dividends often cut in downturns)
  3. Historical dividend growth rates
  4. Regime-switching model (high/low dividend periods)

**Benefits:**
- More realistic modeling of dividend uncertainty
- Better representation of dividend cuts during market stress
- Improved tax planning scenarios

**Implementation Notes:**
- Keep option for fixed dividend yield for simplicity
- Add stochastic dividend yield as advanced option
- Consider correlation with price returns

**Files to modify:**
- `finsim/simulation.py` - Add stochastic dividend model
- `app.py` - Add UI option for dividend volatility
- `tests/test_simulation.py` - Test stochastic dividend scenarios

---

## Enhancement: Implement Regime-Based Monte Carlo Simulation

**Current Behavior:**
- Uses independent, identically distributed (IID) returns from Geometric Brownian Motion
- Each year's return is independent of previous years
- No mean reversion or momentum effects

**Proposed Enhancement:**
- Implement regime-based Monte Carlo that accounts for market cycles
- Model different market regimes (bull, bear, recovery, stagnation)
- Include transition probabilities between regimes
- Incorporate mean reversion and momentum effects observed in real markets

**Academic Support:**
- Research shows regime-based Monte Carlo outperforms traditional IID Monte Carlo by ~25% (lower Brier scores)
- Historical patterns show strong mean reversion after extreme market events
- Traditional Monte Carlo can overstate retirement income by 5-10% compared to historical outcomes
- At 2% real returns, 50% of traditional MC trials are worse than any historical period including Great Depression

**Implementation Approach:**
1. Define market regimes based on historical data:
   - Bull market: High returns, moderate volatility
   - Bear market: Negative returns, high volatility  
   - Recovery: Above-average returns following bear markets
   - Stagnation: Low returns, low volatility

2. Estimate transition matrix from historical data:
   - Probability of staying in same regime
   - Probability of transitioning to other regimes
   - Duration-dependent transitions (longer bull markets more likely to end)

3. Calibrate regime parameters:
   - Mean return and volatility for each regime
   - Use historical sequences to estimate parameters
   - Consider economic indicators if available

**Benefits:**
- More realistic simulation of actual market dynamics
- Better tail risk assessment for retirement planning
- Captures momentum and mean reversion seen in real markets
- Reduces overstatement of safe withdrawal rates

**Implementation Notes:**
- Keep option for traditional IID Monte Carlo for comparison
- Allow users to adjust regime parameters
- Show regime transitions in visualization
- Consider Hidden Markov Model (HMM) for regime detection

**Files to modify:**
- `finsim/simulation.py` - Add RegimeBasedSimulation class
- `finsim/market/models.py` - Create regime detection and transition logic
- `app.py` - Add UI option to choose simulation method
- `tests/test_regime_simulation.py` - Test regime transitions and parameters

**References:**
- Income Laboratory research on MC vs historical simulation
- Kitces research on Historical and Regime-Based Monte Carlo models
- Academic papers on regime-switching models in finance

---

## Other Potential Enhancements

1. **Variable spending strategies** - Adjust spending based on portfolio performance
2. **Rebalancing strategies** - Model different asset allocations over time
3. **Tax-loss harvesting** - Model tax optimization strategies
4. **Social Security optimization** - Model different claiming strategies
5. **Healthcare costs** - Add stochastic healthcare expense modeling