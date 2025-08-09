"""Tests for data fetching utilities."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from finsim.data_fetcher import SSAMortalityFetcher


class TestSSAMortalityFetcher:
    """Test the SSA mortality data fetcher."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = SSAMortalityFetcher()
        assert fetcher.SSA_URL == "https://www.ssa.gov/oact/STATS/table4c6.html"
        assert 65 in fetcher.FALLBACK_MALE
        assert 65 in fetcher.FALLBACK_FEMALE
    
    def test_fallback_data_validity(self):
        """Test that fallback data is valid."""
        fetcher = SSAMortalityFetcher()
        
        # Check male mortality
        for age, rate in fetcher.FALLBACK_MALE.items():
            assert 65 <= age <= 100
            assert 0 < rate < 1
            # Mortality should generally increase with age
            if age > 65:
                assert rate >= fetcher.FALLBACK_MALE.get(age - 1, 0)
        
        # Check female mortality
        for age, rate in fetcher.FALLBACK_FEMALE.items():
            assert 65 <= age <= 100
            assert 0 < rate < 1
            # Mortality should generally increase with age
            if age > 65:
                assert rate >= fetcher.FALLBACK_FEMALE.get(age - 1, 0)
        
        # Female mortality should generally be lower than male
        for age in fetcher.FALLBACK_MALE:
            if age in fetcher.FALLBACK_FEMALE:
                assert fetcher.FALLBACK_FEMALE[age] <= fetcher.FALLBACK_MALE[age]
    
    @patch('finsim.data_fetcher.requests.get')
    def test_fetch_tables_success(self, mock_get):
        """Test successful fetching of mortality tables."""
        # Mock HTML response with simplified table structure
        mock_html = """
        <html>
        <table>
            <tr><th>Age</th><th>Male</th><th>Female</th></tr>
            <tr><td>65</td><td>0.01604</td><td>0.01052</td></tr>
            <tr><td>66</td><td>0.01753</td><td>0.01146</td></tr>
        </table>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fetcher = SSAMortalityFetcher()
        male, female = fetcher.fetch_tables()
        
        assert 65 in male
        assert male[65] == 0.01604
        assert 66 in male
        assert male[66] == 0.01753
        
        assert 65 in female
        assert female[65] == 0.01052
        assert 66 in female
        assert female[66] == 0.01146
    
    @patch('finsim.data_fetcher.requests.get')
    def test_fetch_tables_network_error(self, mock_get):
        """Test fallback when network request fails."""
        mock_get.side_effect = Exception("Network error")
        
        fetcher = SSAMortalityFetcher()
        male, female = fetcher.fetch_tables()
        
        # Should return fallback data
        assert male == fetcher.FALLBACK_MALE
        assert female == fetcher.FALLBACK_FEMALE
    
    @patch('finsim.data_fetcher.requests.get')
    def test_fetch_tables_invalid_html(self, mock_get):
        """Test fallback when HTML parsing fails."""
        mock_response = Mock()
        mock_response.text = "<html>Invalid content</html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fetcher = SSAMortalityFetcher()
        male, female = fetcher.fetch_tables()
        
        # Should return fallback data when parsing fails
        assert male == fetcher.FALLBACK_MALE
        assert female == fetcher.FALLBACK_FEMALE
    
    def test_parse_ssa_page_valid(self):
        """Test parsing valid SSA HTML."""
        html = """
        <table>
            <tr><th>Exact age</th><th>Male qx</th><th>Female qx</th></tr>
            <tr><td>65</td><td>0.01604</td><td>0.01052</td></tr>
            <tr><td>70</td><td>0.02476</td><td>0.01642</td></tr>
            <tr><td>75</td><td>0.03843</td><td>0.02653</td></tr>
        </table>
        """
        
        fetcher = SSAMortalityFetcher()
        male, female = fetcher._parse_ssa_page(html)
        
        assert male[65] == 0.01604
        assert male[70] == 0.02476
        assert male[75] == 0.03843
        
        assert female[65] == 0.01052
        assert female[70] == 0.01642
        assert female[75] == 0.02653
    
    def test_parse_ssa_page_with_noise(self):
        """Test parsing HTML with extra content."""
        html = """
        <p>Some text before</p>
        <table>
            <tr><td>Not relevant</td></tr>
        </table>
        <table>
            <tr><th>Age</th><th>Male</th><th>Female</th><th>Extra</th></tr>
            <tr><td>Age 65</td><td>0.01604</td><td>0.01052</td><td>Note</td></tr>
            <tr><td>66 years</td><td>0.01753*</td><td>0.01146</td><td>*estimated</td></tr>
        </table>
        <p>Some text after</p>
        """
        
        fetcher = SSAMortalityFetcher()
        male, female = fetcher._parse_ssa_page(html)
        
        # Should extract numbers despite formatting
        assert 65 in male
        assert 66 in male
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('finsim.data_fetcher.Path.mkdir')
    def test_save_to_json_default_path(self, mock_mkdir, mock_file):
        """Test saving mortality data to default JSON path."""
        fetcher = SSAMortalityFetcher()
        
        with patch.object(fetcher, 'fetch_tables') as mock_fetch:
            mock_fetch.return_value = (
                {65: 0.01604, 70: 0.02476},
                {65: 0.01052, 70: 0.01642}
            )
            
            result_path = fetcher.save_to_json()
            
            # Check file was written
            mock_file.assert_called_once()
            
            # Check JSON structure
            written_data = ''
            for call in mock_file().write.call_args_list:
                written_data += call[0][0]
            
            data = json.loads(written_data)
            assert data['source'] == fetcher.SSA_URL
            assert '65' in data['male']
            assert data['male']['65'] == 0.01604
            assert '65' in data['female']
            assert data['female']['65'] == 0.01052
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_to_json_custom_path(self, mock_file):
        """Test saving to a custom path."""
        fetcher = SSAMortalityFetcher()
        custom_path = Path("/tmp/custom_mortality.json")
        
        with patch.object(fetcher, 'fetch_tables') as mock_fetch:
            mock_fetch.return_value = (
                {65: 0.01604},
                {65: 0.01052}
            )
            
            with patch.object(Path, 'mkdir'):
                result_path = fetcher.save_to_json(custom_path)
                assert result_path == custom_path