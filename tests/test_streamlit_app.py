"""Tests for Streamlit app components."""

import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_annuity_calculator_with_zero_guarantee():
    """Test that annuity calculator handles zero guarantee months."""
    from finsim import AnnuityCalculator
    
    calc = AnnuityCalculator(age=65)
    
    # Test zero guarantee months for non-life-contingent annuity
    irr = calc.calculate_irr(
        premium=527530,
        monthly_payment=5397,
        guarantee_months=0,
        life_contingent=False
    )
    assert irr == -1.0, "Should return -1.0 for zero guarantee months"
    
    # Test normal case
    irr = calc.calculate_irr(
        premium=527530,
        monthly_payment=5397,
        guarantee_months=120,
        life_contingent=False
    )
    assert -0.05 < irr < 0.05, f"IRR should be reasonable, got {irr}"


def test_annuity_comparison():
    """Test annuity comparison functionality."""
    from finsim import AnnuityCalculator
    
    calc = AnnuityCalculator(age=65)
    
    proposals = [
        {
            'name': 'Proposal A',
            'premium': 527530,
            'monthly_payment': 3516,
            'guarantee_months': 180,
            'life_contingent': True,
            'taxable': False
        },
        {
            'name': 'Proposal B',
            'premium': 527530,
            'monthly_payment': 4058,
            'guarantee_months': 180,
            'life_contingent': False,
            'taxable': False
        },
        {
            'name': 'Proposal C',
            'premium': 527530,
            'monthly_payment': 5397,
            'guarantee_months': 120,
            'life_contingent': False,
            'taxable': False
        }
    ]
    
    df = calc.compare_annuity_options(proposals)
    
    assert len(df) == 3, "Should have 3 proposals"
    assert all(col in df.columns for col in ['Name', 'IRR', 'Total Guaranteed'])
    assert df['Total Guaranteed'].iloc[2] == 5397 * 120


def test_monte_carlo_simulator_initialization():
    """Test Monte Carlo simulator initialization."""
    from finsim import MonteCarloSimulator
    
    sim = MonteCarloSimulator(
        initial_capital=527530,
        target_after_tax_monthly=4000,
        social_security_monthly=2000,
        age=65,
        state="CA",
        filing_status="SINGLE",
        n_simulations=100
    )
    
    assert sim.initial_capital == 527530
    assert sim.n_simulations == 100
    assert sim.age == 65
    assert sim.state == "CA"


@patch('finsim.tax.Microsimulation')
def test_monte_carlo_with_tax_integration(mock_microsim):
    """Test Monte Carlo simulator with tax calculations."""
    from finsim import MonteCarloSimulator
    
    # Mock the microsimulation to avoid PolicyEngine dependencies
    mock_sim_instance = MagicMock()
    mock_microsim.return_value = mock_sim_instance
    
    # Mock tax calculation results
    mock_sim_instance.calculate.return_value.values = np.zeros(100)
    
    sim = MonteCarloSimulator(
        initial_capital=527530,
        target_after_tax_monthly=4000,
        social_security_monthly=2000,
        age=65,
        state="CA",
        filing_status="SINGLE",
        n_simulations=100
    )
    
    # Run short simulation
    results = sim.simulate(n_years=2)
    
    assert 'paths' in results
    assert 'final_values' in results
    assert 'depletion_probability' in results
    assert results['paths'].shape[0] == 100  # n_simulations
    assert results['paths'].shape[1] == 25  # 2 years * 12 months + 1


def test_tax_dataset_structure():
    """Test that tax dataset has required structure."""
    from finsim.tax import MonteCarloDataset
    import tempfile
    
    n_scenarios = 10
    capital_gains = np.random.uniform(0, 50000, n_scenarios)
    social_security = np.full(n_scenarios, 24000)
    ages = np.full(n_scenarios, 65)
    
    dataset = MonteCarloDataset(
        n_scenarios=n_scenarios,
        capital_gains_array=capital_gains,
        social_security_array=social_security,
        ages=ages,
        state="CA",
        year=2025,
        filing_status="SINGLE"
    )
    
    # Generate dataset
    dataset.generate()
    
    # Check that file was created
    assert dataset.file_path.exists()
    
    # Clean up
    dataset.cleanup()
    assert not dataset.file_path.exists()


def test_app_data_flow():
    """Test the data flow through app components."""
    from finsim import MonteCarloSimulator, AnnuityCalculator
    
    # Test values from the app
    settlement = 527530
    monthly_ss = 2000
    age = 65
    
    # Test annuity calculation
    calc = AnnuityCalculator(age=age)
    proposals = [
        {
            'name': 'Test',
            'premium': settlement,
            'monthly_payment': 4000,
            'guarantee_months': 180,
            'life_contingent': False,
            'taxable': False
        }
    ]
    
    df = calc.compare_annuity_options(proposals)
    assert not df.empty
    
    # Test Monte Carlo initialization (not running full simulation)
    sim = MonteCarloSimulator(
        initial_capital=settlement,
        target_after_tax_monthly=4000,
        social_security_monthly=monthly_ss,
        age=age,
        state="CA",
        filing_status="SINGLE",
        n_simulations=100
    )
    
    assert sim.initial_capital == settlement
    assert sim.social_security_monthly == monthly_ss


def test_streamlit_inputs_validation():
    """Test that app handles various input combinations."""
    from finsim import AnnuityCalculator
    
    calc = AnnuityCalculator(age=65)
    
    # Test edge cases
    edge_cases = [
        (100000, 1000, 12, False),  # Low values
        (1000000, 10000, 240, True),  # High values
        (500000, 5000, 1, False),  # Single month
    ]
    
    for premium, payment, months, life_cont in edge_cases:
        irr = calc.calculate_irr(
            premium=premium,
            monthly_payment=payment,
            guarantee_months=months,
            life_contingent=life_cont
        )
        assert isinstance(irr, float), f"IRR should be float for case {premium}, {payment}, {months}"
        assert -1.0 <= irr <= 1.0, f"IRR should be reasonable for case {premium}, {payment}, {months}"


if __name__ == "__main__":
    # Run tests
    test_annuity_calculator_with_zero_guarantee()
    print("✓ Annuity calculator handles zero guarantee months")
    
    test_annuity_comparison()
    print("✓ Annuity comparison works correctly")
    
    test_monte_carlo_simulator_initialization()
    print("✓ Monte Carlo simulator initializes properly")
    
    test_monte_carlo_with_tax_integration()
    print("✓ Monte Carlo integrates with tax calculations")
    
    test_tax_dataset_structure()
    print("✓ Tax dataset has correct structure")
    
    test_app_data_flow()
    print("✓ App data flow works correctly")
    
    test_streamlit_inputs_validation()
    print("✓ Input validation handles edge cases")
    
    print("\nAll tests passed!")