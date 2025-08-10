"""Standalone test for input validation."""

from finsim.portfolio_simulation import validate_inputs


def get_valid_params():
    """Return a set of valid parameters for testing."""
    return {
        'n_simulations': 100,
        'n_years': 30,
        'initial_portfolio': 1_000_000,
        'current_age': 65,
        'social_security': 30_000,
        'pension': 10_000,
        'employment_income': 0,
        'retirement_age': 65,
        'annuity_annual': 0,
        'annuity_guarantee_years': 0,
        'annual_consumption': 60_000,
        'expected_return': 0.07,
        'return_volatility': 0.15,
        'dividend_yield': 0.02,
        'state': 'CA',
        'gender': 'Male',
        'annuity_type': 'Life Only',
        'has_spouse': False,
    }


def test_valid_inputs():
    """Test that valid inputs pass validation."""
    params = get_valid_params()
    try:
        validate_inputs(**params)
        print("✓ Valid inputs accepted")
        return True
    except Exception as e:
        print(f"✗ Valid inputs rejected: {e}")
        return False


def test_negative_simulations():
    """Test that negative n_simulations raises ValueError."""
    params = get_valid_params()
    params['n_simulations'] = -1
    try:
        validate_inputs(**params)
        print("✗ Negative simulations should have been rejected")
        return False
    except ValueError as e:
        if "n_simulations must be positive" in str(e):
            print("✓ Negative simulations correctly rejected")
            return True
        print(f"✗ Wrong error for negative simulations: {e}")
        return False


def test_invalid_state():
    """Test that invalid state code raises ValueError."""
    params = get_valid_params()
    params['state'] = 'ZZ'
    try:
        validate_inputs(**params)
        print("✗ Invalid state should have been rejected")
        return False
    except ValueError as e:
        if "Invalid state" in str(e):
            print("✓ Invalid state correctly rejected")
            return True
        print(f"✗ Wrong error for invalid state: {e}")
        return False


def test_spouse_validation():
    """Test spouse validation."""
    params = get_valid_params()
    params['has_spouse'] = True
    
    # Test missing spouse_age
    try:
        validate_inputs(**params)
        print("✗ Missing spouse_age should have been rejected")
        return False
    except ValueError as e:
        if "spouse_age is required" in str(e):
            print("✓ Missing spouse_age correctly rejected")
        else:
            print(f"✗ Wrong error for missing spouse_age: {e}")
            return False
    
    # Test valid spouse params
    params['spouse_age'] = 63
    params['spouse_gender'] = 'Female'
    try:
        validate_inputs(**params)
        print("✓ Valid spouse parameters accepted")
        return True
    except Exception as e:
        print(f"✗ Valid spouse parameters rejected: {e}")
        return False


def test_boundary_values():
    """Test boundary values."""
    params = get_valid_params()
    
    # Test maximum simulations
    params['n_simulations'] = 100_000
    try:
        validate_inputs(**params)
        print("✓ Maximum simulations (100,000) accepted")
    except Exception as e:
        print(f"✗ Maximum simulations rejected: {e}")
        return False
    
    # Test just over maximum
    params['n_simulations'] = 100_001
    try:
        validate_inputs(**params)
        print("✗ Excessive simulations should have been rejected")
        return False
    except ValueError as e:
        if "n_simulations too large" in str(e):
            print("✓ Excessive simulations correctly rejected")
        else:
            print(f"✗ Wrong error for excessive simulations: {e}")
            return False
    
    return True


def test_extreme_returns():
    """Test extreme return values."""
    params = get_valid_params()
    
    # Test very negative return
    params['expected_return'] = -0.75
    try:
        validate_inputs(**params)
        print("✗ Very negative return should have been rejected")
        return False
    except ValueError as e:
        if "expected_return too low" in str(e):
            print("✓ Very negative return correctly rejected")
        else:
            print(f"✗ Wrong error for negative return: {e}")
            return False
    
    # Test very positive return
    params['expected_return'] = 0.75
    try:
        validate_inputs(**params)
        print("✗ Very positive return should have been rejected")
        return False
    except ValueError as e:
        if "expected_return too high" in str(e):
            print("✓ Very positive return correctly rejected")
        else:
            print(f"✗ Wrong error for positive return: {e}")
            return False
    
    return True


if __name__ == "__main__":
    print("Testing Input Validation for FinSim")
    print("=" * 60)
    
    tests = [
        test_valid_inputs,
        test_negative_simulations,
        test_invalid_state,
        test_spouse_validation,
        test_boundary_values,
        test_extreme_returns,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All input validation tests passed!")
    else:
        exit(1)