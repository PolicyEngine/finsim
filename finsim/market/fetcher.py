"""Market data fetching and caching."""

import logging
import pickle
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FundData:
    """Data for a fund or ETF."""

    ticker: str
    name: str
    annual_return: float  # Real (inflation-adjusted) annual return %
    volatility: float  # Annual volatility %
    dividend_yield: float  # Current dividend yield %
    expense_ratio: float  # Annual expense ratio %
    data_points: int = 0  # Number of data points used

    @property
    def net_return(self) -> float:
        """Return after expenses."""
        return self.annual_return - self.expense_ratio


class MarketDataFetcher:
    """Fetches and caches market data from various sources."""

    # Common ticker symbols
    TICKER_VT = "VT"  # Vanguard Total World Stock ETF
    TICKER_VOO = "VOO"  # Vanguard S&P 500 ETF
    TICKER_BND = "BND"  # Vanguard Total Bond Market ETF
    TICKER_GLD = "GLD"  # SPDR Gold Shares

    def __init__(
        self, cache_dir: str | None = None, cache_expiry: timedelta = timedelta(days=1)
    ):
        """Initialize the market data fetcher.

        Args:
            cache_dir: Directory for caching data
            cache_expiry: How long to cache data
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".finsim" / "cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = cache_expiry

    def fetch_fund_data(
        self, ticker: str, years: int = 10, inflation_rate: float = 2.5
    ) -> FundData:
        """Fetch fund data with caching.

        Args:
            ticker: Fund ticker symbol
            years: Years of historical data to use
            inflation_rate: Annual inflation rate for real return calculation

        Returns:
            FundData object with statistics
        """
        # Check cache first
        cache_key = f"{ticker}_{years}_{inflation_rate}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        # Fetch from source
        try:
            fund_data = self._fetch_from_yfinance(ticker, years, inflation_rate)
            self._save_to_cache(cache_key, fund_data)
            return fund_data
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {ticker}: {e}") from e

    def _fetch_from_yfinance(
        self, ticker: str, years: int, inflation_rate: float
    ) -> FundData:
        """Fetch data from yfinance.

        Args:
            ticker: Fund ticker symbol
            years: Years of historical data
            inflation_rate: Annual inflation rate

        Returns:
            FundData object
        """
        try:
            import yfinance as yf
        except ImportError as e:
            raise ImportError("yfinance required for market data fetching") from e

        # Fetch historical data
        fund = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)

        hist = fund.history(start=start_date, end=end_date, interval="1d")

        if hist.empty:
            raise ValueError(f"No data available for {ticker}")

        # Calculate returns
        returns = hist["Close"].pct_change().dropna()

        # Calculate statistics
        annual_return, volatility = self._calculate_statistics(returns)

        # Adjust for inflation
        real_return = annual_return - inflation_rate

        # Get fund info
        info = fund.info
        name = info.get("longName", ticker)
        dividend_yield = info.get("dividendYield", 0.0) * 100  # Convert to %
        expense_ratio = info.get("expenseRatio", 0.0) * 100  # Convert to %

        return FundData(
            ticker=ticker,
            name=name,
            annual_return=real_return,
            volatility=volatility,
            dividend_yield=dividend_yield,
            expense_ratio=expense_ratio,
            data_points=len(returns),
        )

    def _calculate_statistics(self, returns: pd.Series) -> tuple[float, float]:
        """Calculate annualized return and volatility.

        Args:
            returns: Daily returns series

        Returns:
            Tuple of (annual_return %, annual_volatility %)
        """
        # Annualized return (geometric mean)
        mean_return = (1 + returns).prod() ** (252 / len(returns)) - 1
        annual_return = mean_return * 100

        # Annualized volatility
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252) * 100

        return annual_return, annual_vol

    def _get_from_cache(self, cache_key: str) -> FundData | None:
        """Get data from cache if available and not expired.

        Args:
            cache_key: Cache key

        Returns:
            FundData if cached and valid, None otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            return None

        # Check if expired
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > self.cache_expiry:
            return None

        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: FundData):
        """Save data to cache.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
