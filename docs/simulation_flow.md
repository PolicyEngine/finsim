# Simulation Flow

This page documents the complete flow of the FinSim Monte Carlo simulation engine.

## High-Level Architecture

```{mermaid}
flowchart TB
    Start([Start Simulation]) --> Init[Initialize Parameters]
    Init --> GenReturns[Generate Return Matrix<br/>N simulations × M years]
    GenReturns --> LoadMort[Load Mortality Tables]
    LoadMort --> Loop{For Each Year<br/>1 to M}
    
    Loop --> CheckMort[Check Mortality]
    CheckMort --> ApplyGrowth[Apply Market Returns<br/>from Pre-generated Matrix]
    ApplyGrowth --> CalcDiv[Calculate Dividends<br/>2% of Portfolio]
    CalcDiv --> CalcIncome[Calculate Total Income<br/>Wages + SS + Pension + Dividends]
    CalcIncome --> CalcWithdraw[Calculate Withdrawal<br/>Consumption + Prior Taxes - Income]
    CalcWithdraw --> CalcGains[Calculate Capital Gains<br/>from Withdrawal]
    CalcGains --> CalcTax[Calculate This Year's Tax<br/>via PolicyEngine]
    CalcTax --> UpdatePort[Update Portfolio<br/>Growth - Withdrawal]
    UpdatePort --> CheckFail{Portfolio < 0?}
    
    CheckFail -->|Yes| MarkFail[Mark as Failed]
    CheckFail -->|No| NextYear
    MarkFail --> NextYear{Next Year?}
    
    NextYear -->|Yes| Loop
    NextYear -->|No| Results[Calculate Results]
    Results --> End([End Simulation])
```

## Detailed Annual Simulation Loop

```{mermaid}
flowchart LR
    subgraph Year N
        A[Start Year N] --> B[Age = Current + N]
        B --> C{Check<br/>Mortality?}
        C -->|Alive| D[Get Growth Factor<br/>from Matrix[sim, year]]
        C -->|Dead| E[No Growth]
        D --> F[Portfolio × Growth]
        E --> F
        F --> G[Dividends =<br/>Portfolio × 2%]
    end
    
    subgraph Income Calculation
        G --> H[Wages if Age < Retirement]
        H --> I[SS + Pension + Annuity]
        I --> J[Total = Guaranteed + Dividends]
    end
    
    subgraph Withdrawal & Taxes
        J --> K[Need = Consumption +<br/>Last Year's Taxes]
        K --> L[Withdraw = max(0, Need - Income)]
        L --> M[Capital Gains =<br/>Withdrawal × Gain%]
        M --> N[Calculate This Year's Tax<br/>for Next Year Payment]
    end
    
    subgraph Update
        N --> O[Portfolio -= Withdrawal]
        O --> P{Portfolio > 0?}
        P -->|Yes| Q[Continue]
        P -->|No| R[Mark Failed]
    end
```

## Return Generation Matrix

The simulation pre-generates all returns to ensure independence:

```{mermaid}
graph TD
    subgraph Return Matrix
        R[Return Generator] --> M[Matrix: N_sims × N_years]
        M --> S1[Sim 1: 1.07, 0.95, 1.12, ...]
        M --> S2[Sim 2: 1.03, 1.08, 0.92, ...]
        M --> S3[Sim 3: 1.15, 1.01, 1.09, ...]
        M --> SN[Sim N: 0.98, 1.11, 1.05, ...]
    end
    
    style M fill:#f9f,stroke:#333,stroke-width:2px
```

**Key Features:**
- All returns generated upfront (fixes repeated value bug)
- Normal distribution with fat tails (2% chance of extreme moves)
- Independent across simulations and years
- Capped at 4σ to prevent overflow

## Tax Calculation Flow

```{mermaid}
flowchart TD
    subgraph Income Components
        W[Wages/Salary] --> TI[Taxable Income]
        SS[Social Security] --> TI
        P[Pension] --> TI
        D[Dividends] --> TI
        CG[Capital Gains] --> TI
    end
    
    TI --> PE[PolicyEngine-US]
    
    subgraph PolicyEngine Calculations
        PE --> FED[Federal Tax<br/>Progressive Brackets]
        PE --> STATE[State Tax<br/>Varies by State]
        PE --> QDIV[Qualified Dividend<br/>Preferential Rates]
        PE --> LTCG[Long-term Cap Gains<br/>0%, 15%, or 20%]
        PE --> NIIT[Net Investment Tax<br/>3.8% if High Income]
    end
    
    FED --> TOTAL[Total Tax Due]
    STATE --> TOTAL
    QDIV --> TOTAL
    LTCG --> TOTAL
    NIIT --> TOTAL
    
    TOTAL --> NEXT[Pay Next Year]
```

## Withdrawal Logic

The "next-year tax payment" approach avoids circular dependency:

```{mermaid}
graph LR
    subgraph Year N
        C1[Calculate Consumption Need] --> W1[Withdrawal = Need - Income]
        W1 --> T1[Calculate Tax on Year N Income]
        T1 --> S1[Store Tax for Year N+1]
    end
    
    subgraph Year N+1
        S1 --> C2[Consumption + Year N Tax]
        C2 --> W2[Withdrawal = Need - Income]
        W2 --> T2[Calculate Tax on Year N+1 Income]
    end
    
    style S1 fill:#faa,stroke:#333,stroke-width:2px
```

## Portfolio Evolution Scenarios

```{mermaid}
graph TD
    Start[Initial Portfolio<br/>$500,000] --> Y1{Year 1-5}
    
    Y1 -->|Lucky: +15%/yr| L1[Portfolio: $1M<br/>Dividends: $20k]
    Y1 -->|Average: +7%/yr| A1[Portfolio: $700k<br/>Dividends: $14k]
    Y1 -->|Unlucky: -5%/yr| U1[Portfolio: $350k<br/>Dividends: $7k]
    
    L1 --> Y10L{Year 10}
    A1 --> Y10A{Year 10}
    U1 --> Y10U{Year 10}
    
    Y10L -->|Compounds Freely| L2[Portfolio: $5M+<br/>No Withdrawals Needed]
    Y10A -->|Steady Withdrawals| A2[Portfolio: $600k<br/>Sustainable]
    Y10U -->|High Withdrawals| U2[Portfolio: $0<br/>FAILED]
    
    style U2 fill:#f99,stroke:#333,stroke-width:2px
    style L2 fill:#9f9,stroke:#333,stroke-width:2px
```

## Key Insights

### Why Pre-generate Returns?
- **Bug Prevention**: Avoids repeated values that plagued earlier versions
- **Performance**: Faster than generating in-loop
- **Testing**: Easier to validate distribution properties
- **Reproducibility**: Can save/load return matrices

### Why Next-Year Tax Payment?
- **Avoids Circular Logic**: Don't need to estimate tax rate
- **Realistic**: Matches how taxes work in reality
- **Accurate**: Use actual income, not estimates

### Portfolio Dynamics
When portfolios grow large:
1. Dividends increase proportionally
2. Eventually dividends > consumption
3. Withdrawals → 0
4. Portfolio compounds without drag
5. Creates realistic "wealth explosion" for lucky paths

## Implementation Files

- **`finsim/portfolio_simulation.py`**: Main simulation loop
- **`finsim/return_generator.py`**: Return matrix generation
- **`finsim/tax.py`**: PolicyEngine integration
- **`finsim/mortality.py`**: SSA mortality tables
- **`tests/test_return_generator.py`**: Comprehensive test suite

## Performance Metrics

For 1,000 simulations × 30 years:
- Return generation: ~0.5 seconds
- Main simulation: ~25 seconds (mostly tax calculations)
- Results processing: ~1 second
- Total: ~30 seconds

## Validation

The simulation has been validated against:
- Historical market returns
- SSA mortality tables
- PolicyEngine tax calculations
- Monte Carlo best practices

## Common Parameters

| Parameter | Typical Value | Range |
|-----------|--------------|-------|
| Expected Return | 7% | 4-10% |
| Volatility | 15% | 10-25% |
| Dividend Yield | 2% | 0-4% |
| Withdrawal Rate | 4% | 2-6% |
| Simulations | 1,000 | 100-10,000 |
| Years | 30 | 10-50 |