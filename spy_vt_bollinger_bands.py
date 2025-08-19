"""Create a chart comparing SPY and VT with Bollinger Bands."""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Set up the plot style
plt.style.use('seaborn-v0_8-darkgrid')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Define parameters
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 3)  # 3 years of data (need more for 200-day MA)
bb_period = 200  # Bollinger Band period
bb_std = 2  # Number of standard deviations

# Fetch data for SPY and VT
print("Fetching data for SPY and VT...")
spy = yf.download('SPY', start=start_date, end=end_date, progress=False)
vt = yf.download('VT', start=start_date, end=end_date, progress=False)

def calculate_bollinger_bands(data, period=20, num_std=2):
    """Calculate Bollinger Bands for given data."""
    result = pd.DataFrame(index=data.index)
    result['Close'] = data['Close']
    result['SMA'] = result['Close'].rolling(window=period).mean()
    result['STD'] = result['Close'].rolling(window=period).std()
    result['Upper'] = result['SMA'] + (result['STD'] * num_std)
    result['Lower'] = result['SMA'] - (result['STD'] * num_std)
    return result

# Calculate Bollinger Bands
spy_bb = calculate_bollinger_bands(spy, bb_period, bb_std)
vt_bb = calculate_bollinger_bands(vt, bb_period, bb_std)

# Plot SPY
ax1.plot(spy_bb.index, spy_bb['Close'], label='SPY Price', color='blue', linewidth=1.5)
ax1.plot(spy_bb.index, spy_bb['SMA'], label=f'{bb_period}-day SMA', color='orange', linewidth=1, alpha=0.8)
ax1.plot(spy_bb.index, spy_bb['Upper'], label='Upper Band', color='red', linewidth=0.8, linestyle='--', alpha=0.7)
ax1.plot(spy_bb.index, spy_bb['Lower'], label='Lower Band', color='green', linewidth=0.8, linestyle='--', alpha=0.7)
ax1.fill_between(spy_bb.index, spy_bb['Lower'], spy_bb['Upper'], alpha=0.1, color='gray')

# Highlight when price touches bands
spy_mask_upper = spy_bb['Close'] >= spy_bb['Upper']
spy_mask_lower = spy_bb['Close'] <= spy_bb['Lower']
spy_upper_touches = spy_bb.loc[spy_mask_upper, 'Close']
spy_lower_touches = spy_bb.loc[spy_mask_lower, 'Close']
if len(spy_upper_touches) > 0:
    ax1.scatter(spy_upper_touches.index, spy_upper_touches.values, color='red', s=20, alpha=0.6, zorder=5)
if len(spy_lower_touches) > 0:
    ax1.scatter(spy_lower_touches.index, spy_lower_touches.values, color='green', s=20, alpha=0.6, zorder=5)

ax1.set_title('SPY (S&P 500 ETF) with Bollinger Bands', fontsize=14, fontweight='bold')
ax1.set_ylabel('Price ($)', fontsize=12)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)

# Plot VT
ax2.plot(vt_bb.index, vt_bb['Close'], label='VT Price', color='purple', linewidth=1.5)
ax2.plot(vt_bb.index, vt_bb['SMA'], label=f'{bb_period}-day SMA', color='orange', linewidth=1, alpha=0.8)
ax2.plot(vt_bb.index, vt_bb['Upper'], label='Upper Band', color='red', linewidth=0.8, linestyle='--', alpha=0.7)
ax2.plot(vt_bb.index, vt_bb['Lower'], label='Lower Band', color='green', linewidth=0.8, linestyle='--', alpha=0.7)
ax2.fill_between(vt_bb.index, vt_bb['Lower'], vt_bb['Upper'], alpha=0.1, color='gray')

# Highlight when price touches bands
vt_mask_upper = vt_bb['Close'] >= vt_bb['Upper']
vt_mask_lower = vt_bb['Close'] <= vt_bb['Lower']
vt_upper_touches = vt_bb.loc[vt_mask_upper, 'Close']
vt_lower_touches = vt_bb.loc[vt_mask_lower, 'Close']
if len(vt_upper_touches) > 0:
    ax2.scatter(vt_upper_touches.index, vt_upper_touches.values, color='red', s=20, alpha=0.6, zorder=5)
if len(vt_lower_touches) > 0:
    ax2.scatter(vt_lower_touches.index, vt_lower_touches.values, color='green', s=20, alpha=0.6, zorder=5)

ax2.set_title('VT (Total World Stock ETF) with Bollinger Bands', fontsize=14, fontweight='bold')
ax2.set_xlabel('Date', fontsize=12)
ax2.set_ylabel('Price ($)', fontsize=12)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)

# Rotate x-axis labels
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Add a main title
fig.suptitle('SPY vs VT: 200-Day Bollinger Bands Analysis', fontsize=16, fontweight='bold', y=1.02)

plt.tight_layout()

# Calculate and display statistics
print("\n" + "="*60)
print("BOLLINGER BAND STATISTICS")
print("="*60)

# SPY statistics
spy_touches_upper = len(spy_upper_touches)
spy_touches_lower = len(spy_lower_touches)
spy_current_price = spy_bb['Close'].iloc[-1]
spy_current_sma = spy_bb['SMA'].iloc[-1]
spy_current_upper = spy_bb['Upper'].iloc[-1]
spy_current_lower = spy_bb['Lower'].iloc[-1]
spy_bb_width = spy_current_upper - spy_current_lower
spy_position = (spy_current_price - spy_current_lower) / spy_bb_width

print(f"\nSPY (S&P 500):")
print(f"  Current Price: ${spy_current_price:.2f}")
print(f"  200-day SMA: ${spy_current_sma:.2f}")
print(f"  Upper Band: ${spy_current_upper:.2f}")
print(f"  Lower Band: ${spy_current_lower:.2f}")
print(f"  Band Width: ${spy_bb_width:.2f}")
print(f"  Position in Band: {spy_position:.1%} (0%=lower, 100%=upper)")
print(f"  Times touched upper band: {spy_touches_upper}")
print(f"  Times touched lower band: {spy_touches_lower}")

# VT statistics
vt_touches_upper = len(vt_upper_touches)
vt_touches_lower = len(vt_lower_touches)
vt_current_price = vt_bb['Close'].iloc[-1]
vt_current_sma = vt_bb['SMA'].iloc[-1]
vt_current_upper = vt_bb['Upper'].iloc[-1]
vt_current_lower = vt_bb['Lower'].iloc[-1]
vt_bb_width = vt_current_upper - vt_current_lower
vt_position = (vt_current_price - vt_current_lower) / vt_bb_width

print(f"\nVT (Total World Stock):")
print(f"  Current Price: ${vt_current_price:.2f}")
print(f"  200-day SMA: ${vt_current_sma:.2f}")
print(f"  Upper Band: ${vt_current_upper:.2f}")
print(f"  Lower Band: ${vt_current_lower:.2f}")
print(f"  Band Width: ${vt_bb_width:.2f}")
print(f"  Position in Band: {vt_position:.1%} (0%=lower, 100%=upper)")
print(f"  Times touched upper band: {vt_touches_upper}")
print(f"  Times touched lower band: {vt_touches_lower}")

# Performance comparison
spy_return = (spy_current_price / spy_bb['Close'].iloc[0] - 1) * 100
vt_return = (vt_current_price / vt_bb['Close'].iloc[0] - 1) * 100

print(f"\nPerformance Since Start:")
print(f"  SPY: {spy_return:.1f}%")
print(f"  VT: {vt_return:.1f}%")
print(f"  Outperformance (SPY - VT): {spy_return - vt_return:.1f}%")

# Volatility comparison
spy_volatility = spy_bb['STD'].iloc[-1]
vt_volatility = vt_bb['STD'].iloc[-1]

print(f"\nCurrent Volatility (200-day std dev):")
print(f"  SPY: ${spy_volatility:.2f}")
print(f"  VT: ${vt_volatility:.2f}")

print("\n" + "="*60)

# Save the figure
plt.savefig('spy_vt_bollinger_bands.png', dpi=300, bbox_inches='tight')
print("\nChart saved as 'spy_vt_bollinger_bands.png'")

# Show the plot (commented out to avoid hanging)
# plt.show()