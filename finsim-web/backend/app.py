"""Flask backend for FinSim web application."""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pandas as pd
import numpy as np
from io import StringIO
import json
from typing import Dict, List, Any, Optional
import simulation
from scenarios import SCENARIOS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])

VERSION = "1.0.0"


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': VERSION
    })


@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get all available scenarios."""
    return jsonify({
        'scenarios': SCENARIOS
    })


@app.route('/api/scenarios/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    
    if not scenario:
        return jsonify({'error': f'Scenario {scenario_id} not found'}), 404
    
    return jsonify(scenario)


@app.route('/api/market/calibrate', methods=['POST'])
def calibrate_market():
    """Fetch and calibrate market data for a given ticker."""
    data = request.json
    ticker = data.get('ticker', 'VT')
    lookback_years = data.get('lookback_years', 10)
    
    try:
        # Try professional models first for best predictions
        try:
            from professional_models import ProfessionalMarketCalibrator
            
            calibrator = ProfessionalMarketCalibrator()
            
            # Try GARCH model first (best for volatility forecasting)
            result = calibrator.calibrate_with_arch(ticker, lookback_years)
            
            if result:
                # Get dividend yield separately
                import yfinance as yf
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                div_yield = info.get('dividendYield', 0.02) * 100
                
                return jsonify({
                    'ticker': ticker,
                    'price_return': round(result['expected_return'] * 100, 1),
                    'volatility': round(result['volatility'] * 100, 1),
                    'dividend_yield': round(min(div_yield, 5.0), 2),
                    'actual_years': lookback_years,
                    'total_return': round(result['expected_return'] * 100 + div_yield, 1),
                    # Uncertainty metrics
                    'tail_index': result.get('tail_index', 30),
                    'var_95_daily': result.get('var_95_daily', -2.0),
                    'calibration_method': 'GARCH-t'
                })
        except ImportError:
            pass  # Professional packages not installed, use fallback
        
        # Fallback to simple but robust historical calibration
        import yfinance as yf
        from datetime import datetime, timedelta
        from scipy import stats
        
        # Fetch historical data
        ticker_obj = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * lookback_years)
        
        hist = ticker_obj.history(start=start_date, end=end_date, interval="1d")
        
        if hist.empty:
            return jsonify({'error': f'No data found for ticker {ticker}'}), 404
        
        # Calculate statistics
        actual_years = (hist.index[-1] - hist.index[0]).days / 365.25
        
        # Calculate daily returns
        daily_returns = hist['Close'].pct_change().dropna()
        
        # Calculate annualized return using CAGR (more robust than mean)
        total_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
        annualized_return = (1 + total_return) ** (1/actual_years) - 1
        
        # Calculate annualized volatility
        daily_volatility = daily_returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        # Calculate uncertainty metrics
        n_years = len(daily_returns) / 252
        return_stderr = annualized_volatility / np.sqrt(n_years)
        
        # Test for fat tails
        kurtosis = stats.kurtosis(daily_returns)
        skewness = stats.skew(daily_returns)
        
        # Convert to percentages
        mean_price_return = annualized_return * 100
        volatility = annualized_volatility * 100
        
        # Get current dividend yield
        info = ticker_obj.info
        div_yield_raw = info.get('dividendYield', 0.02)
        current_div_yield = div_yield_raw * 100 if div_yield_raw < 1 else div_yield_raw
        
        return jsonify({
            'ticker': ticker,
            'price_return': round(mean_price_return, 1),
            'volatility': round(volatility, 1),
            'dividend_yield': round(min(current_div_yield, 5.0), 2),
            'actual_years': round(actual_years, 1),
            'total_return': round(mean_price_return + current_div_yield, 1),
            # Uncertainty metrics
            'return_stderr': round(return_stderr * 100, 2),
            'skewness': round(skewness, 3),
            'excess_kurtosis': round(kurtosis, 3),
            'calibration_method': 'Historical-Robust'
        })
        
    except Exception as e:
        # Return sensible defaults if fetch fails
        return jsonify({
            'ticker': ticker,
            'price_return': 7.0,
            'volatility': 18.0,
            'dividend_yield': 2.0,
            'actual_years': lookback_years,
            'total_return': 9.0,
            'return_stderr': 2.0,
            'error': str(e),
            'calibration_method': 'Default'
        })


@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """Run a single simulation."""
    data = request.json
    
    # Validate request
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    scenario_id = data.get('scenario_id')
    spending_level = data.get('spending_level')
    parameters = data.get('parameters')
    
    if not scenario_id:
        return jsonify({'error': 'scenario_id is required'}), 400
    
    if not spending_level:
        return jsonify({'error': 'spending_level is required'}), 400
    
    if not parameters:
        return jsonify({'error': 'parameters are required'}), 400
    
    # Check if scenario exists
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if not scenario:
        return jsonify({'error': f'Invalid scenario ID: {scenario_id}'}), 400
    
    try:
        # Run simulation
        results = simulation.run_single_simulation(
            scenario=scenario,
            spending_level=spending_level,
            parameters=parameters
        )
        
        return jsonify({
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulate/batch', methods=['POST'])
def run_batch_simulation():
    """Run batch simulations for multiple scenarios and spending levels."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    scenario_ids = data.get('scenario_ids', [])
    spending_levels = data.get('spending_levels', [])
    parameters = data.get('parameters')
    
    if not scenario_ids:
        return jsonify({'error': 'scenario_ids is required'}), 400
    
    if not spending_levels:
        return jsonify({'error': 'spending_levels is required'}), 400
    
    if not parameters:
        return jsonify({'error': 'parameters are required'}), 400
    
    # Validate scenarios
    scenarios = []
    for sid in scenario_ids:
        scenario = next((s for s in SCENARIOS if s['id'] == sid), None)
        if not scenario:
            return jsonify({'error': f'Invalid scenario ID: {sid}'}), 400
        scenarios.append(scenario)
    
    try:
        # Run batch simulation
        results = simulation.run_batch_simulation(
            scenarios=scenarios,
            spending_levels=spending_levels,
            parameters=parameters
        )
        
        return jsonify({
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/confidence', methods=['POST'])
def analyze_confidence():
    """Analyze confidence thresholds for scenarios."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    scenario_ids = data.get('scenario_ids', [])
    confidence_levels = data.get('confidence_levels', [90, 75, 50])
    parameters = data.get('parameters')
    
    if not scenario_ids:
        return jsonify({'error': 'scenario_ids is required'}), 400
    
    if not parameters:
        return jsonify({'error': 'parameters are required'}), 400
    
    # Validate scenarios
    scenarios = []
    for sid in scenario_ids:
        scenario = next((s for s in SCENARIOS if s['id'] == sid), None)
        if not scenario:
            return jsonify({'error': f'Invalid scenario ID: {sid}'}), 400
        scenarios.append(scenario)
    
    try:
        # Analyze confidence thresholds
        results = simulation.analyze_confidence_thresholds(
            scenarios=scenarios,
            confidence_levels=confidence_levels,
            parameters=parameters
        )
        
        return jsonify({
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_results():
    """Export simulation results in various formats."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    format_type = data.get('format', 'csv')
    results = data.get('results', [])
    
    if not results:
        return jsonify({'error': 'No results to export'}), 400
    
    if format_type == 'csv':
        # Convert to CSV
        df = pd.DataFrame(results)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=simulation_results.csv'}
        )
    
    elif format_type == 'json':
        return jsonify(results)
    
    else:
        return jsonify({'error': f'Unsupported format: {format_type}'}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)