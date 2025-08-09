"""Streamlit app for retirement decision analysis."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from finsim import MonteCarloSimulator, AnnuityCalculator


# Page config
st.set_page_config(
    page_title="Retirement Decision Tool",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Retirement Settlement Decision Tool")
st.markdown("""
Compare structured settlement annuities with index fund investments, 
using tax-aware Monte Carlo simulations powered by PolicyEngine-US.
""")

# Sidebar inputs
st.sidebar.header("📊 Basic Information")

age = st.sidebar.number_input("Current Age", min_value=50, max_value=100, value=65)
state = st.sidebar.selectbox("State", ["CA", "NY", "TX", "FL", "IL", "PA"], index=0)
filing_status = st.sidebar.selectbox("Filing Status", ["SINGLE", "JOINT"], index=0)

st.sidebar.header("💵 Settlement Details")
settlement_amount = st.sidebar.number_input(
    "Settlement Amount ($)", 
    min_value=0, 
    value=527_530, 
    step=10_000,
    format="%d"
)

st.sidebar.header("🏦 Social Security")
monthly_ss_benefit = st.sidebar.number_input(
    "Monthly SS Benefit ($)", 
    min_value=0, 
    value=2_000, 
    step=100,
    format="%d"
)

st.sidebar.header("📈 Market Assumptions")
use_historical = st.sidebar.checkbox("Calibrate to historical data", value=False)
if use_historical:
    ticker = st.sidebar.text_input("Ticker Symbol", value="VT")
    lookback_years = st.sidebar.slider("Years of History", 10, 50, 30)

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📝 Annuity Options", "📈 Analysis", "📊 Detailed Results"])

# Tab 1: Annuity Options
with tab1:
    st.header("Enter Annuity Proposals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Proposal A")
        a_monthly = st.number_input("Monthly Payment A ($)", value=3_516, step=100, key="a_monthly")
        a_guarantee = st.number_input("Guarantee Period A (years)", value=15, step=1, key="a_guarantee")
        a_life = st.checkbox("Life Contingent", value=True, key="a_life")
    
    with col2:
        st.subheader("Proposal B")
        b_monthly = st.number_input("Monthly Payment B ($)", value=4_058, step=100, key="b_monthly")
        b_guarantee = st.number_input("Guarantee Period B (years)", value=15, step=1, key="b_guarantee")
        b_life = st.checkbox("Life Contingent", value=False, key="b_life")
    
    st.subheader("Proposal C")
    col3, col4 = st.columns(2)
    with col3:
        c_monthly = st.number_input("Monthly Payment C ($)", value=5_397, step=100, key="c_monthly")
        c_guarantee = st.number_input("Guarantee Period C (years)", value=10, step=1, key="c_guarantee")
    with col4:
        c_life = st.checkbox("Life Contingent", value=False, key="c_life")

# Tab 2: Analysis
with tab2:
    st.header("Comparative Analysis")
    
    # Create annuity proposals
    proposals = [
        {
            'name': 'Proposal A',
            'premium': settlement_amount,
            'monthly_payment': a_monthly,
            'guarantee_months': int(a_guarantee * 12),
            'life_contingent': a_life,
            'taxable': False  # Settlement annuities are tax-free
        },
        {
            'name': 'Proposal B',
            'premium': settlement_amount,
            'monthly_payment': b_monthly,
            'guarantee_months': int(b_guarantee * 12),
            'life_contingent': b_life,
            'taxable': False
        },
        {
            'name': 'Proposal C',
            'premium': settlement_amount,
            'monthly_payment': c_monthly,
            'guarantee_months': int(c_guarantee * 12),
            'life_contingent': c_life,
            'taxable': False
        }
    ]
    
    # Calculate annuity metrics
    annuity_calc = AnnuityCalculator(age=age)
    annuity_df = annuity_calc.compare_annuity_options(proposals)
    
    # Display annuity comparison
    st.subheader("Annuity Comparison")
    st.dataframe(annuity_df.style.format({
        'Premium': '${:,.0f}',
        'Monthly Payment': '${:,.0f}',
        'Annual Payment': '${:,.0f}',
        'Total Guaranteed': '${:,.0f}',
        'IRR': '{:.1%}',
        'Guarantee Period': '{:.0f} years'
    }))
    
    # Monte Carlo simulations
    st.subheader("Monte Carlo Analysis")
    
    n_simulations = st.selectbox("Number of Simulations", [1000, 5000, 10000, 50000], index=2)
    
    # Run simulations for each proposal
    selected_proposal = st.selectbox(
        "Select Proposal to Simulate",
        ['Proposal A', 'Proposal B', 'Proposal C']
    )
    
    selected_idx = ['Proposal A', 'Proposal B', 'Proposal C'].index(selected_proposal)
    target_monthly = proposals[selected_idx]['monthly_payment']
    guarantee_years = proposals[selected_idx]['guarantee_months'] // 12
    
    # Create and run simulation
    with st.spinner(f"Running {n_simulations:,} simulations..."):
        sim = MonteCarloSimulator(
            initial_capital=settlement_amount,
            target_after_tax_monthly=target_monthly,
            social_security_monthly=monthly_ss_benefit,
            age=age,
            state=state,
            filing_status=filing_status,
            n_simulations=n_simulations
        )
        
        # Calibrate to historical data if requested
        if use_historical:
            sim.fit_historical(ticker=ticker, lookback_years=lookback_years)
        
        # Run simulation
        results = sim.simulate(n_years=guarantee_years)
        
        # Compare to annuity
        comparison = sim.compare_to_annuity(
            annuity_monthly_payment=target_monthly,
            annuity_guarantee_years=guarantee_years,
            simulation_results=results
        )
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Depletion Risk", f"{results['depletion_probability']:.1%}")
    with col2:
        st.metric("Median Final Value", f"${results['median_final_value']:,.0f}")
    with col3:
        st.metric("P(MC > Annuity)", f"{comparison['probability_mc_exceeds_annuity']:.1%}")
    with col4:
        st.metric("Mean Taxes Paid", f"${np.mean(results['total_taxes']):,.0f}")

# Tab 3: Detailed Results
with tab3:
    if 'results' in locals():
        st.header("Portfolio Value Over Time")
        
        # Sample paths for visualization
        n_display = min(100, n_simulations)
        sample_indices = np.random.choice(n_simulations, n_display, replace=False)
        
        fig = go.Figure()
        
        # Add individual paths
        months = results['paths'].shape[1] - 1
        for i in sample_indices:
            fig.add_trace(go.Scatter(
                x=list(range(months + 1)),
                y=results['paths'][i],
                mode='lines',
                line=dict(width=0.5, color='lightblue'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add percentile bands
        percentiles_over_time = np.percentile(results['paths'], [5, 25, 50, 75, 95], axis=0)
        
        fig.add_trace(go.Scatter(
            x=list(range(months + 1)),
            y=percentiles_over_time[2],  # Median
            mode='lines',
            name='Median',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=list(range(months + 1)),
            y=percentiles_over_time[0],  # 5th percentile
            mode='lines',
            name='5th Percentile',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=list(range(months + 1)),
            y=percentiles_over_time[4],  # 95th percentile
            mode='lines',
            name='95th Percentile',
            line=dict(color='green', width=1, dash='dash')
        ))
        
        # Add annuity comparison line
        annuity_value = settlement_amount
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Depleted"
        )
        
        fig.update_layout(
            title=f"Monte Carlo Simulation - {selected_proposal}",
            xaxis_title="Months",
            yaxis_title="Portfolio Value ($)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribution of final values
        st.subheader("Distribution of Final Values")
        
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=results['final_values'],
            nbinsx=50,
            name='Final Values',
            marker_color='blue',
            opacity=0.7
        ))
        
        fig2.add_vline(
            x=0, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Depleted"
        )
        
        fig2.add_vline(
            x=settlement_amount, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Initial Capital"
        )
        
        fig2.update_layout(
            title="Distribution of Final Portfolio Values",
            xaxis_title="Portfolio Value ($)",
            yaxis_title="Frequency",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        
        summary_df = pd.DataFrame({
            'Metric': [
                'Annuity Total (Guaranteed)',
                'MC Mean After-Tax Total',
                'MC Median After-Tax Total',
                'MC Mean Final Value',
                'MC Median Final Value',
                'Depletion Probability',
                'P(MC > Annuity)'
            ],
            'Value': [
                f"${comparison['annuity_total_guaranteed']:,.0f}",
                f"${comparison['mc_mean_total_after_tax']:,.0f}",
                f"${comparison['mc_median_total_after_tax']:,.0f}",
                f"${results['mean_final_value']:,.0f}",
                f"${results['median_final_value']:,.0f}",
                f"{results['depletion_probability']:.1%}",
                f"{comparison['probability_mc_exceeds_annuity']:.1%}"
            ]
        })
        
        st.table(summary_df)

# Footer
st.markdown("---")
st.markdown("""
**Note:** Tax calculations use PolicyEngine-US for accuracy. 
Results include federal and state taxes, Social Security taxation, 
and all applicable deductions including the OBBBA senior deduction.

**Disclaimer:** This tool is for educational purposes only. 
Consult with qualified financial and tax professionals before making decisions.
""")