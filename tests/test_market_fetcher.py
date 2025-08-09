"""Tests for market data fetching module."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from finsim.market.fetcher import MarketDataFetcher, FundData


class TestFundData:
    """Test the FundData dataclass."""
    
    def test_fund_data_creation(self):
        """Test creating FundData object."""
        data = FundData(
            ticker="VT",
            name="Vanguard Total World Stock ETF",
            annual_return=7.5,
            volatility=16.2,
            dividend_yield=2.1,
            expense_ratio=0.07,
            data_points=1000
        )
        
        assert data.ticker == "VT"
        assert data.annual_return == 7.5
        assert data.volatility == 16.2
        assert data.dividend_yield == 2.1
        assert data.expense_ratio == 0.07
        assert data.data_points == 1000
    
    def test_fund_data_real_return(self):
        """Test calculating real return after expenses."""
        data = FundData(
            ticker="VT",
            name="Test Fund",
            annual_return=8.0,
            volatility=15.0,
            dividend_yield=2.0,
            expense_ratio=0.10
        )
        
        # Real return should subtract expense ratio
        assert data.net_return == 7.9  # 8.0 - 0.10


class TestMarketDataFetcher:
    """Test the market data fetcher."""
    
    def test_initialization(self):
        """Test fetcher initialization."""
        fetcher = MarketDataFetcher()
        assert fetcher.cache_dir.exists()
        assert fetcher.cache_expiry == timedelta(days=1)
    
    def test_initialization_with_custom_cache(self):
        """Test fetcher with custom cache settings."""
        fetcher = MarketDataFetcher(
            cache_dir="/tmp/test_cache",
            cache_expiry=timedelta(hours=6)
        )
        assert str(fetcher.cache_dir) == "/tmp/test_cache"
        assert fetcher.cache_expiry == timedelta(hours=6)
    
    @patch('yfinance.Ticker')
    def test_fetch_fund_data_success(self, mock_ticker_class):
        """Test successful fund data fetching."""
        # Mock yfinance response
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock historical data
        dates = pd.date_range(end=datetime.now(), periods=252*3, freq='D')
        prices = 100 * np.exp(np.random.normal(0.0003, 0.01, len(dates)).cumsum())
        mock_history = pd.DataFrame({
            'Close': prices,
            'Dividends': np.random.uniform(0, 0.1, len(dates))
        }, index=dates)
        mock_ticker.history.return_value = mock_history
        
        # Mock info
        mock_ticker.info = {
            'longName': 'Vanguard Total World Stock ETF',
            'dividendYield': 0.021,
            'expenseRatio': 0.0007
        }
        
        fetcher = MarketDataFetcher()
        fund_data = fetcher.fetch_fund_data("VT", years=3)
        
        assert fund_data.ticker == "VT"
        assert fund_data.name == "Vanguard Total World Stock ETF"
        assert 0 <= fund_data.annual_return <= 50  # Reasonable range
        assert 0 <= fund_data.volatility <= 50
        assert fund_data.dividend_yield == 2.1
        assert fund_data.expense_ratio == 0.07
    
    @patch('yfinance.Ticker')
    def test_fetch_fund_data_with_inflation_adjustment(self, mock_ticker_class):
        """Test fetching with inflation adjustment."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        # Create synthetic data with known return
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        # 10% nominal return
        prices = 100 * np.exp(np.linspace(0, 0.10, len(dates)))
        mock_history = pd.DataFrame({'Close': prices}, index=dates)
        mock_ticker.history.return_value = mock_history
        mock_ticker.info = {}
        
        fetcher = MarketDataFetcher()
        fund_data = fetcher.fetch_fund_data(
            "TEST", 
            years=1,
            inflation_rate=2.5  # 2.5% inflation
        )
        
        # Real return should be approximately nominal - inflation
        # 10% - 2.5% = 7.5%
        assert 7.0 <= fund_data.annual_return <= 8.0
    
    @patch('yfinance.Ticker')
    def test_fetch_fund_data_network_error(self, mock_ticker_class):
        """Test handling network errors."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.side_effect = Exception("Network error")
        
        fetcher = MarketDataFetcher()
        
        with pytest.raises(ValueError, match="Failed to fetch data"):
            fetcher.fetch_fund_data("INVALID")
    
    @patch('yfinance.Ticker')
    def test_fetch_fund_data_empty_response(self, mock_ticker_class):
        """Test handling empty data response."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        
        fetcher = MarketDataFetcher()
        
        with pytest.raises(ValueError, match="No data available"):
            fetcher.fetch_fund_data("NODATA")
    
    def test_cache_functionality(self):
        """Test that caching works correctly."""
        fetcher = MarketDataFetcher()
        
        # Mock the _fetch_from_yfinance method
        with patch.object(fetcher, '_fetch_from_yfinance') as mock_fetch:
            mock_fetch.return_value = FundData(
                ticker="VT",
                name="Test",
                annual_return=7.0,
                volatility=15.0,
                dividend_yield=2.0,
                expense_ratio=0.07
            )
            
            # First call should fetch
            data1 = fetcher.fetch_fund_data("VT")
            assert mock_fetch.call_count == 1
            
            # Second call should use cache
            data2 = fetcher.fetch_fund_data("VT")
            assert mock_fetch.call_count == 1  # No additional call
            
            assert data1.annual_return == data2.annual_return
    
    def test_cache_expiry(self):
        """Test that cache expires correctly."""
        fetcher = MarketDataFetcher(cache_expiry=timedelta(seconds=0))
        
        with patch.object(fetcher, '_fetch_from_yfinance') as mock_fetch:
            mock_fetch.return_value = FundData(
                ticker="VT",
                name="Test",
                annual_return=7.0,
                volatility=15.0,
                dividend_yield=2.0,
                expense_ratio=0.07
            )
            
            # Both calls should fetch due to immediate expiry
            fetcher.fetch_fund_data("VT")
            fetcher.fetch_fund_data("VT")
            assert mock_fetch.call_count == 2
    
    def test_calculate_statistics(self):
        """Test calculation of return statistics."""
        fetcher = MarketDataFetcher()
        
        # Create known price series
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        # Constant 10% annual return, no volatility
        prices = 100 * np.exp(np.linspace(0, 0.10, len(dates)))
        
        returns = prices.pct_change().dropna()
        annual_return, volatility = fetcher._calculate_statistics(returns)
        
        # Should be close to 10% return, near-zero volatility
        assert 9.5 <= annual_return <= 10.5
        assert volatility < 1.0  # Very low volatility
    
    def test_common_tickers(self):
        """Test that common ticker constants are available."""
        assert MarketDataFetcher.TICKER_VT == "VT"  # Total World
        assert MarketDataFetcher.TICKER_VOO == "VOO"  # S&P 500
        assert MarketDataFetcher.TICKER_BND == "BND"  # Bonds
        assert MarketDataFetcher.TICKER_GLD == "GLD"  # Gold