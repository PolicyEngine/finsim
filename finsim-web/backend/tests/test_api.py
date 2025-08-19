"""Test-driven development for the FinSim API."""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns OK."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'version' in data


class TestScenariosEndpoint:
    """Test the scenarios configuration endpoint."""
    
    def test_get_available_scenarios(self, client):
        """Test getting list of available scenarios."""
        response = client.get('/api/scenarios')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'scenarios' in data
        assert len(data['scenarios']) == 4
        
        # Check first scenario structure
        scenario = data['scenarios'][0]
        assert 'id' in scenario
        assert 'name' in scenario
        assert 'description' in scenario
        assert 'has_annuity' in scenario
    
    def test_get_specific_scenario(self, client):
        """Test getting a specific scenario by ID."""
        response = client.get('/api/scenarios/stocks_only')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['id'] == 'stocks_only'
        assert data['name'] == '100% Stocks (VT)'
        assert data['has_annuity'] is False


class TestSimulationEndpoint:
    """Test the simulation endpoint."""
    
    def test_run_simulation_single_scenario(self, client):
        """Test running a simulation for a single scenario."""
        request_data = {
            'scenario_id': 'stocks_only',
            'spending_level': 50000,
            'parameters': {
                'current_age': 65,
                'gender': 'Male',
                'social_security': 24000,
                'state': 'CA',
                'expected_return': 7.0,
                'return_volatility': 18.0
            }
        }
        
        with patch('simulation.run_single_simulation') as mock_sim:
            mock_sim.return_value = {
                'success_rate': 0.85,
                'median_final': 250000,
                'p10_final': 50000,
                'p90_final': 750000
            }
            
            response = client.post('/api/simulate',
                                 json=request_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'results' in data
            assert data['results']['success_rate'] == 0.85
            assert 'median_final' in data['results']
    
    def test_run_batch_simulation(self, client):
        """Test running simulations for multiple spending levels."""
        request_data = {
            'scenario_ids': ['stocks_only', 'annuity_a'],
            'spending_levels': [40000, 50000, 60000],
            'parameters': {
                'current_age': 65,
                'gender': 'Male',
                'social_security': 24000,
                'state': 'CA'
            }
        }
        
        with patch('simulation.run_batch_simulation') as mock_sim:
            mock_sim.return_value = [
                {
                    'scenario': 'stocks_only',
                    'spending': 40000,
                    'success_rate': 0.95
                },
                {
                    'scenario': 'stocks_only',
                    'spending': 50000,
                    'success_rate': 0.85
                }
            ]
            
            response = client.post('/api/simulate/batch',
                                 json=request_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'results' in data
            assert len(data['results']) >= 2
    
    def test_invalid_scenario_id(self, client):
        """Test that invalid scenario ID returns error."""
        request_data = {
            'scenario_id': 'invalid_scenario',
            'spending_level': 50000,
            'parameters': {'current_age': 65}
        }
        
        response = client.post('/api/simulate',
                              json=request_data,
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_missing_required_parameters(self, client):
        """Test that missing parameters returns error."""
        request_data = {
            'scenario_id': 'stocks_only',
            'spending_level': 50000
            # Missing parameters
        }
        
        response = client.post('/api/simulate',
                              json=request_data,
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestConfidenceAnalysisEndpoint:
    """Test the confidence analysis endpoint."""
    
    def test_analyze_confidence_levels(self, client):
        """Test analyzing confidence thresholds."""
        request_data = {
            'scenario_ids': ['stocks_only', 'annuity_a'],
            'confidence_levels': [90, 75, 50],
            'parameters': {
                'current_age': 65,
                'gender': 'Male',
                'social_security': 24000,
                'state': 'CA'
            }
        }
        
        with patch('simulation.analyze_confidence_thresholds') as mock_analyze:
            mock_analyze.return_value = {
                'stocks_only': {90: 45000, 75: 55000, 50: 65000},
                'annuity_a': {90: 61000, 75: 66000, 50: 70000}
            }
            
            response = client.post('/api/analyze/confidence',
                                 json=request_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'results' in data
            assert 'stocks_only' in data['results']
            assert data['results']['stocks_only']['90'] == 45000


class TestExportEndpoint:
    """Test the export functionality."""
    
    def test_export_results_csv(self, client):
        """Test exporting results as CSV."""
        request_data = {
            'format': 'csv',
            'results': [
                {'scenario': 'stocks_only', 'spending': 50000, 'success_rate': 0.85}
            ]
        }
        
        response = client.post('/api/export',
                              json=request_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
        assert b'scenario,spending,success_rate' in response.data
    
    def test_export_results_json(self, client):
        """Test exporting results as JSON."""
        request_data = {
            'format': 'json',
            'results': [
                {'scenario': 'stocks_only', 'spending': 50000, 'success_rate': 0.85}
            ]
        }
        
        response = client.post('/api/export',
                              json=request_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'