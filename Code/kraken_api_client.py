"""
Kraken API client for fetching OHLCV data with rate limiting and retry logic.
"""

import http.client
import urllib.request
import urllib.parse
import hashlib
import hmac
import base64
import json
import time
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kraken pair names for 14 cryptocurrencies
CRYPTO_PAIRS = {
    'avalanche': 'AVAXUSD',
    'axie_infinity': 'AXSUSD',
    'binance_coin': 'BNBUSD',
    'bitcoin': 'XXBTZUSD',
    'chainlink': 'LINKUSD',
    'ethereum': 'XETHZUSD',
    #'fantom': 'FTMUSDT',
    'injective': 'INJUSD',
    'litecoin': 'XLTCZUSD',
    'maker': 'SKYUSD',
    'render': 'RENDERUSD',
    'solana': 'SOLUSD',
    'the_graph': 'GRTUSD',
    'toncoin': 'TONUSD',
    'tron': 'TRXUSD',
}


class KrakenAPIClient:
    """Client for fetching OHLCV data from Kraken API."""
    
    def __init__(self, base_url: str = "https://api.kraken.com", rate_limit_delay: float = 0.1):
        """
        Initialize Kraken API client.
        
        Args:
            base_url: Kraken API base URL
            rate_limit_delay: Delay between requests in seconds (respects ~15 req/sec limit)
        """
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, path: str, query: Dict, max_retries: int = 3) -> Dict:
        """
        Make HTTP request with retry logic.
        
        Args:
            path: API endpoint path
            query: Query parameters
            max_retries: Maximum number of retry attempts
            
        Returns:
            Parsed JSON response
        """
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                
                url = self.base_url + path
                query_str = urllib.parse.urlencode(query)
                url += "?" + query_str
                
                req = urllib.request.Request(
                    method="GET",
                    url=url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                response = urllib.request.urlopen(req, timeout=30)
                data = json.loads(response.read().decode())
                
                if data.get('error'):
                    raise Exception(f"Kraken API error: {data['error']}")
                
                return data
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
    
    def get_ohlc(self, pair: str, interval: int = 1440, since: Optional[int] = None) -> List[List]:
        """
        Fetch OHLCV data from Kraken.
        
        Args:
            pair: Trading pair (e.g., 'XXBTZUSD')
            interval: Candle interval in minutes (1440 = daily)
            since: Unix timestamp to fetch data after
            
        Returns:
            List of OHLCV candles: [timestamp, open, high, low, close, vwap, volume, count]
        """
        query = {
            'pair': pair,
            'interval': interval,
        }
        
        if since:
            query['since'] = since
        
        response = self._make_request('/0/public/OHLC', query)
        
        # Kraken returns data for the pair, extract it
        result = response.get('result', {})
        
        # Find the pair key (might have whitespace or formatting differences)
        for key in result.keys():
            if key.upper() == pair.upper():
                candles = result[key]
                return candles
        
        logger.warning(f"No data found for pair {pair}")
        return []
    
    def backfill_crypto(self, crypto_name: str, pair: str, days_back: int = None, 
                        output_dir: str = 'data/interim/backfilled', from_inception: bool = True) -> str:
        """
        Backfill historical OHLCV data for a cryptocurrency.
        
        Args:
            crypto_name: Human-readable name (e.g., 'bitcoin')
            pair: Kraken pair name (e.g., 'XXBTZUSD')
            days_back: Days of history to fetch (default None = fetch all available)
            output_dir: Directory to save CSV files
            from_inception: If True, fetch from earliest available data (overrides days_back)
            
        Returns:
            Path to saved CSV file
        """
        logger.info(f"Starting backfill for {crypto_name} ({pair})...")
        
        all_candles = []
        now = int(time.time())
        
        # Determine start date
        if from_inception:
            # Start from year 2000 (covers all crypto history since Bitcoin started ~2009)
            since = int(datetime(2000, 1, 1).timestamp())
        elif days_back:
            since = int((now - (days_back * 86400)))  # 86400 seconds = 1 day
        else:
            # Default: fetch 10 years of data
            since = int((now - (10 * 365 * 86400)))
        
        while since < now:
            try:
                logger.info(f"  Fetching from {datetime.fromtimestamp(since).strftime('%Y-%m-%d')}")
                
                candles = self.get_ohlc(pair, interval=1440, since=since)
                
                if not candles:
                    logger.info(f"  No more data available")
                    break
                
                all_candles.extend(candles)
                
                # Move since to the last candle timestamp + 1 day
                if candles:
                    last_ts = int(candles[-1][0])
                    since = last_ts + 86400
                
            except Exception as e:
                logger.error(f"  Error fetching data: {e}")
                break
        
        if not all_candles:
            logger.warning(f"No data fetched for {crypto_name}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
        )
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
        
        # Convert OHLCV to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['count'] = pd.to_numeric(df['count'], errors='coerce')
        
        # Sort by timestamp ascending
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
        
        # Drop unnecessary columns
        df = df.drop(columns=['count', 'vwap'])
        
        # Log statistics
        logger.info(f"  Fetched {len(df)} candles")
        logger.info(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        logger.info(f"  Volume range: {df['volume'].min():.2f} to {df['volume'].max():.2f}")
        
        # Save to CSV
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f'{crypto_name}_backfilled.csv')
        df.to_csv(output_file, index=False)
        
        logger.info(f"  Saved to {output_file}")
        return output_file


def backfill_all_cryptos(output_dir: str = 'data/interim/backfilled', days_back: int = None, from_inception: bool = True):
    """
    Backfill data for all 15 cryptocurrencies.
    
    Args:
        output_dir: Directory to save CSV files
        days_back: Days of history to fetch (default None = fetch all available)
        from_inception: If True, fetch from earliest available data (default True)
    """
    client = KrakenAPIClient()
    
    results = {}
    for crypto_name, pair in CRYPTO_PAIRS.items():
        try:
            output_file = client.backfill_crypto(crypto_name, pair, days_back=days_back, 
                                                output_dir=output_dir, from_inception=from_inception)
            if output_file:
                results[crypto_name] = 'SUCCESS'
            else:
                results[crypto_name] = 'FAILED (no data)'
        except Exception as e:
            logger.error(f"Failed to backfill {crypto_name}: {e}")
            results[crypto_name] = f'FAILED ({e})'
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("BACKFILL SUMMARY")
    logger.info("="*60)
    for crypto_name, status in results.items():
        logger.info(f"{crypto_name:20s} : {status}")
    
    success_count = sum(1 for s in results.values() if s == 'SUCCESS')
    logger.info(f"\nTotal: {success_count}/{len(CRYPTO_PAIRS)} successful")


if __name__ == '__main__':
    backfill_all_cryptos()
