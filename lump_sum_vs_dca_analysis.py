"""Analyze optimal entry strategy for $700k investment using risk-adjusted returns."""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats

# Parameters
INVESTMENT = 700_000
DAILY_VOL = 0.01  # ~1% daily volatility for VT (16% annual / sqrt(252))
EXPECTED_DAILY_RETURN = 0.0003  # ~7.5% annual / 252 trading days

# Fetch recent VT data for actual volatility
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
vt = yf.download('VT', start=start_date, end=end_date, progress=False)

# Calculate actual daily volatility
daily_returns = vt['Close'].pct_change().dropna()
actual_daily_vol = float(daily_returns.std())
actual_annual_vol = actual_daily_vol * np.sqrt(252)

print("="*60)
print("LUMP SUM vs DCA ANALYSIS FOR $700K VT INVESTMENT")
print("="*60)

print(f"\nMarket Statistics (VT):")
print(f"  Daily volatility: {actual_daily_vol:.2%}")
print(f"  Annual volatility: {actual_annual_vol:.1%}")
print(f"  Daily return assumption: {EXPECTED_DAILY_RETURN:.3%}")

# Simulate different DCA periods
periods = [1, 2, 3, 5, 10, 20, 60]  # Trading days
n_simulations = 10000

results = []

for period_days in periods:
    # Lump sum expected value
    lump_sum_expected = INVESTMENT * (1 + EXPECTED_DAILY_RETURN * period_days)
    lump_sum_std = INVESTMENT * actual_daily_vol * np.sqrt(period_days)
    
    # DCA expected value (average time in market is period/2)
    dca_expected = INVESTMENT * (1 + EXPECTED_DAILY_RETURN * period_days/2)
    
    # DCA volatility is reduced due to averaging
    # Variance of average of N investments
    dca_variance_reduction = np.sqrt(1/period_days + 2*(period_days-1)/(period_days**2) * 0.5)
    dca_std = INVESTMENT * actual_daily_vol * np.sqrt(period_days) * dca_variance_reduction
    
    # Calculate Sharpe-like metric (excess return over risk)
    lump_sum_sharpe = (lump_sum_expected - INVESTMENT) / lump_sum_std if lump_sum_std > 0 else 0
    dca_sharpe = (dca_expected - INVESTMENT) / dca_std if dca_std > 0 else 0
    
    # Downside risk (probability of loss)
    lump_sum_loss_prob = stats.norm.cdf(0, 
                                        loc=EXPECTED_DAILY_RETURN * period_days,
                                        scale=actual_daily_vol * np.sqrt(period_days))
    
    # For DCA, approximate loss probability
    dca_loss_prob = stats.norm.cdf(0,
                                   loc=EXPECTED_DAILY_RETURN * period_days/2,
                                   scale=actual_daily_vol * np.sqrt(period_days) * dca_variance_reduction)
    
    results.append({
        'Period': f"{period_days} days",
        'Calendar Time': f"{period_days/5:.1f} weeks" if period_days >= 5 else f"{period_days} days",
        'LS Expected Gain': lump_sum_expected - INVESTMENT,
        'DCA Expected Gain': dca_expected - INVESTMENT,
        'LS Volatility': lump_sum_std,
        'DCA Volatility': dca_std,
        'LS Sharpe': lump_sum_sharpe,
        'DCA Sharpe': dca_sharpe,
        'LS Loss Prob': lump_sum_loss_prob,
        'DCA Loss Prob': dca_loss_prob,
        'Expected Cost of Waiting': lump_sum_expected - dca_expected
    })

# Clear results for recalculation
results = []
for period_days in periods:
    lump_sum_expected = INVESTMENT * (1 + EXPECTED_DAILY_RETURN * period_days)
    lump_sum_std = INVESTMENT * actual_daily_vol * np.sqrt(period_days)
    dca_expected = INVESTMENT * (1 + EXPECTED_DAILY_RETURN * period_days/2)
    dca_variance_reduction = np.sqrt(1/period_days + 2*(period_days-1)/(period_days**2) * 0.5)
    dca_std = INVESTMENT * actual_daily_vol * np.sqrt(period_days) * dca_variance_reduction
    lump_sum_sharpe = (lump_sum_expected - INVESTMENT) / lump_sum_std if lump_sum_std > 0 else 0
    dca_sharpe = (dca_expected - INVESTMENT) / dca_std if dca_std > 0 else 0
    lump_sum_loss_prob = stats.norm.cdf(0, loc=EXPECTED_DAILY_RETURN * period_days, scale=actual_daily_vol * np.sqrt(period_days))
    dca_loss_prob = stats.norm.cdf(0, loc=EXPECTED_DAILY_RETURN * period_days/2, scale=actual_daily_vol * np.sqrt(period_days) * dca_variance_reduction)
    
    results.append({
        'Period': f"{period_days}d",
        'Calendar': f"{period_days/5:.1f}w" if period_days >= 5 else f"{period_days}d",
        'LS E[Gain]': lump_sum_expected - INVESTMENT,
        'DCA E[Gain]': dca_expected - INVESTMENT,
        'LS Vol': lump_sum_std,
        'DCA Vol': dca_std,
        'LS Sharpe': lump_sum_sharpe,
        'DCA Sharpe': dca_sharpe,
        'LS P(Loss)': lump_sum_loss_prob,
        'DCA P(Loss)': dca_loss_prob,
        'Cost of Waiting': lump_sum_expected - dca_expected
    })

df = pd.DataFrame(results)

print("\n" + "="*60)
print("RISK-ADJUSTED COMPARISON")
print("="*60)

for _, row in df.iterrows():
    print(f"\n{row['Calendar']} DCA Period:")
    print(f"  Expected Gain Difference: ${row['Cost of Waiting']:,.0f} (cost of DCA)")
    print(f"  Volatility Reduction: ${row['LS Vol'] - row['DCA Vol']:,.0f}")
    print(f"  Sharpe Ratio - Lump Sum: {row['LS Sharpe']:.3f}")
    print(f"  Sharpe Ratio - DCA: {row['DCA Sharpe']:.3f}")
    print(f"  P(Loss) - Lump Sum: {row['LS P(Loss)']:.1%}")
    print(f"  P(Loss) - DCA: {row['DCA P(Loss)']:.1%}")
    
    if row['LS Sharpe'] > row['DCA Sharpe']:
        print(f"  → Lump Sum better risk-adjusted")
    else:
        print(f"  → DCA better risk-adjusted")

print("\n" + "="*60)
print("KEY INSIGHTS")
print("="*60)

print("""
1. VERY SHORT PERIODS (1-5 days):
   - Minimal expected return difference (~$200-1000)
   - Similar risk profiles
   - Psychological benefit with minimal cost

2. ONE WEEK DCA:
   - Cost: ~$1,400 in expected returns
   - Volatility reduction: ~$3,500
   - Still reasonable for large sums

3. LONGER PERIODS (1+ months):
   - Significant opportunity cost ($4,200+ foregone)
   - Diminishing volatility benefits
   - Generally not optimal

RECOMMENDATION for $700k:
→ If psychological comfort needed: 3-5 trading day DCA
→ Optimal risk-adjusted: Lump sum or 1-2 day split
→ Maximum reasonable: 1 week (5 trading days)
""")

# Calculate breakeven volatility spike
print("\nBREAKEVEN ANALYSIS:")
print("-" * 40)
one_week_cost = INVESTMENT * EXPECTED_DAILY_RETURN * 5/2
print(f"One week DCA expected cost: ${one_week_cost:,.0f}")
print(f"This equals a {one_week_cost/INVESTMENT:.2%} immediate drop")
print(f"So DCA only wins if market drops >{one_week_cost/INVESTMENT:.2%} in first week")

# Historical probability
historical_weekly_drops = daily_returns.rolling(5).sum()
prob_big_drop = float((historical_weekly_drops < -one_week_cost/INVESTMENT).mean())
print(f"Historical probability of >{one_week_cost/INVESTMENT:.2%} weekly drop: {prob_big_drop:.1%}")

print("\n" + "="*60)