"""
Kraken API client for live cryptocurrency data fetching
Handles rate limiting, error handling, and data parsing
"""
import requests
import time
import logging
from datetime import datetime, timezone
import pandas as pd
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kraken API configuration
KRAKEN_API_BASE = "https://api.kraken.com/0/public"
KRAKEN_RATE_LIMIT = 15  # requests per second (public API)

# Mapping of cryptocurrency names to Kraken pair codes (14 cryptocurrencies)
# Must match EXACTLY with kraken_api_client.py CRYPTO_PAIRS
CRYPTO_PAIRS = {
    'avalanche': 'AVAXUSD',
    'axie_infinity': 'AXSUSD',
    'binance_coin': 'BNBUSD',
    'bitcoin': 'XXBTZUSD',  # Note: XXBTZUSD (with Z), not XXBTUSD
    'chainlink': 'LINKUSD',
    'ethereum': 'XETHZUSD',
    'injective': 'INJUSD',
    'litecoin': 'XLTCZUSD',
    'maker': 'SKYUSD',
    'render': 'RENDERUSD',
    'solana': 'SOLUSD',
    'the_graph': 'GRTUSD',
    'toncoin': 'TONUSD',
    'tron': 'TRXUSD',
}


class KrakenLiveFetcher:
    """
    Kraken API client for fetching live OHLCV cryptocurrency data
    Implements rate limiting and error handling
    """
    
    def __init__(self, rate_limit: int = KRAKEN_RATE_LIMIT):
        """
        Initialize Kraken API client
        
        Args:
            rate_limit: Maximum requests per second (default 15 for public API)
        """
        self.base_url = KRAKEN_API_BASE
        self.rate_limit = rate_limit
        self.min_interval = 1.0 / rate_limit  # Minimum time between requests
        self.last_request_time = 0
        self.session = requests.Session()
        logger.info(f"✅ KrakenLiveFetcher initialized (rate limit: {rate_limit} req/sec)")
    
    def _respect_rate_limit(self) -> None:
        """
        Enforce rate limiting to avoid hitting API caps
        """
        elapsed = time.time() - self.last_request_time
        wait_time = self.min_interval - elapsed
        
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def get_current_ohlc(self, pair: str, interval: int = 1440, timeout: int = 10) -> Optional[Dict]:
        """
        Fetch current OHLCV data from Kraken
        
        Args:
            pair: Kraken pair code (e.g., 'XXBTZUSD', 'XETHZUSD')
            interval: Candle interval in minutes (default: 1440 = daily, matching Phase 0 training data)
                      Options: 1, 5, 15, 30, 60, 240, 1440
            timeout: Request timeout in seconds
            
        Returns:
            dict: Response from Kraken API or None if failed
            
        Example response:
        {
            "result": {
                "XXBTZUSD": [
                    [timestamp, "open", "high", "low", "close", "vwap", "volume", "count"],
                    ...
                ]
            }
        }
        """
        self._respect_rate_limit()
        
        url = f"{self.base_url}/OHLC"
        params = {
            'pair': pair,
            'interval': interval
        }
        
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for Kraken API errors
            if data.get('error'):
                logger.error(f"Kraken API error for {pair}: {data['error']}")
                return None
            
            logger.debug(f"✅ Fetched OHLC for {pair}")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {pair} (exceeded {timeout}s)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error fetching {pair}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {pair}: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error for {pair}: {e}")
            return None
    
    def parse_ohlc_response(self, raw_response: Dict, pair: str) -> Optional[pd.DataFrame]:
        """
        Parse Kraken OHLC response into DataFrame
        
        Args:
            raw_response: Raw API response from get_current_ohlc()
            pair: Kraken pair code (e.g., 'XXBTUSD')
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, vwap, volume, count
            or None if parsing failed
        """
        try:
            if not raw_response or 'result' not in raw_response:
                logger.error(f"Invalid response format for {pair}")
                return None
            
            data = raw_response.get('result', {}).get(pair)
            
            if not data or len(data) == 0:
                logger.warning(f"No data returned for {pair}")
                return None
            
            # Create DataFrame from response
            df = pd.DataFrame(
                data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
            )
            
            # Convert to numeric types
            for col in ['open', 'high', 'low', 'close', 'vwap', 'volume', 'count']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert timestamp to UTC datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
            
            logger.info(f"✅ Parsed {len(df)} records for {pair}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing {pair} response: {e}")
            return None
    
    def get_latest_candle(self, pair: str, interval: int = 1440) -> Optional[Dict]:
        """
        Get the most recent candle for a cryptocurrency pair
        
        Args:
            pair: Kraken pair code
            interval: Candle interval in minutes (default: 1440 = daily, matching Phase 0 training)
            
        Returns:
            dict with keys: timestamp, open, high, low, close, volume, cryptocurrency, created_at
            Returns None if fetch/parse failed
        """
        raw = self.get_current_ohlc(pair, interval=interval)
        
        if raw is None:
            return None
        
        df = self.parse_ohlc_response(raw, pair)
        
        if df is None or len(df) == 0:
            return None
        
        # Get latest candle (usually the one being formed)
        latest = df.iloc[-1]
        
        return {
            'timestamp': latest['timestamp'],
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest['volume'],
            'pair': pair,
            'interval': interval,
            'created_at': datetime.now(timezone.utc)
        }
    
    def fetch_multiple_pairs(self, pairs: List[str], interval: int = 1440) -> pd.DataFrame:
        """
        Fetch OHLCV data for multiple cryptocurrency pairs
        
        Args:
            pairs: List of Kraken pair codes
            interval: Candle interval in minutes (default: 1440 = daily, matching Phase 0 training)
            
        Returns:
            DataFrame with combined data from all pairs (or empty if all failed)
        """
        all_data = []
        
        for pair in pairs:
            try:
                raw = self.get_current_ohlc(pair, interval=interval)
                if raw is None:
                    continue
                
                df = self.parse_ohlc_response(raw, pair)
                if df is not None and len(df) > 0:
                    df['pair'] = pair
                    all_data.append(df)
                    
            except Exception as e:
                logger.error(f"Error fetching {pair}: {e}")
                continue
        
        if not all_data:
            logger.warning("No data fetched for any pairs")
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"✅ Fetched {len(combined)} records across {len(pairs)} pairs")
        return combined
    
    def get_server_time(self) -> Optional[datetime]:
        """
        Get current Kraken server time (useful for debugging)
        
        Returns:
            datetime object or None if request failed
        """
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                f"{self.base_url}/Time",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if 'result' in data and 'unixtime' in data['result']:
                timestamp = data['result']['unixtime']
                # Use timezone-aware UTC instead of deprecated utcfromtimestamp
                server_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                logger.info(f"✅ Kraken server time: {server_time}")
                return server_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching server time: {e}")
            return None
    
    def close(self) -> None:
        """Close HTTP session"""
        self.session.close()
        logger.info("✅ Kraken API session closed")


# Example usage
if __name__ == "__main__":
    # Initialize fetcher
    fetcher = KrakenLiveFetcher()
    
    # Test: Get server time
    print("\n📍 Testing Kraken connectivity...")
    server_time = fetcher.get_server_time()
    
    # Test: Fetch Bitcoin latest candle (using correct pair: XXBTZUSD with Z)
    print("\n📍 Fetching Bitcoin (XXBTZUSD) latest candle...")
    btc_data = fetcher.get_latest_candle('XXBTZUSD')
    if btc_data:
        print(f"✅ Bitcoin latest price: ${btc_data['close']:.2f}")
        print(f"   Open: ${btc_data['open']:.2f}")
        print(f"   High: ${btc_data['high']:.2f}")
        print(f"   Low:  ${btc_data['low']:.2f}")
    
    # Test: Fetch multiple pairs from CRYPTO_PAIRS (correct 14)
    print("\n📍 Fetching multiple cryptocurrencies...")
    pairs = ['XXBTZUSD', 'XETHZUSD', 'XLTCZUSD']
    df = fetcher.fetch_multiple_pairs(pairs)
    if not df.empty:
        print(f"\n✅ Fetched data:")
        print(df[['timestamp', 'close', 'volume', 'pair']].tail())
    
    fetcher.close()
