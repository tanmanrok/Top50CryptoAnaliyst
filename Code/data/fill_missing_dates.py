#!/usr/bin/env python
"""
Fill missing dates in cryptocurrency price data
Fetches specific dates from Kraken API and loads into database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.kraken_live_fetcher import KrakenLiveFetcher, CRYPTO_PAIRS
from data.db_connection import engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_kraken_history(pair: str, interval: int = 1440) -> pd.DataFrame:
    """Fetch entire history from Kraken for a pair"""
    fetcher = KrakenLiveFetcher()
    
    try:
        response = fetcher.get_current_ohlc(pair, interval=interval)
        
        if not response or 'result' not in response:
            return None
        
        pair_data = response['result'].get(pair, [])
        
        if not pair_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(pair_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        logger.info(f"✅ Fetched {len(df)} records for {pair}")
        return df
        
    except Exception as e:
        logger.error(f"❌ Error fetching {pair}: {e}")
        return None


def load_prices_to_db(crypto_name: str, df: pd.DataFrame) -> int:
    """Load price data to database, handling duplicates"""
    if df is None or len(df) == 0:
        return 0
    
    df['cryptocurrency'] = crypto_name
    stored_count = 0
    
    try:
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    query = text("""
                        INSERT INTO prices 
                        (cryptocurrency, timestamp, open, high, low, close, volume)
                        VALUES 
                        (:cryptocurrency, :timestamp, :open, :high, :low, :close, :volume)
                        ON CONFLICT (cryptocurrency, timestamp) DO UPDATE
                        SET open = :open, high = :high, low = :low, close = :close, volume = :volume
                    """)
                    
                    conn.execute(query, {
                        'cryptocurrency': row['cryptocurrency'],
                        'timestamp': row['timestamp'],
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']),
                    })
                    stored_count += 1
                    
                except Exception as e:
                    logger.debug(f"Row insert error for {crypto_name} @ {row['timestamp']}: {e}")
        
        logger.info(f"✅ {crypto_name}: Stored {stored_count} records")
        return stored_count
        
    except Exception as e:
        logger.error(f"❌ Error loading {crypto_name}: {e}")
        return 0


def main():
    logger.info("="*70)
    logger.info("🔧 FILLING MISSING CRYPTOCURRENCY DATES")
    logger.info("="*70 + "\n")
    
    total_stored = 0
    
    for crypto_name, pair in CRYPTO_PAIRS.items():
        logger.info(f"\nProcessing {crypto_name} ({pair})...")
        
        # Fetch all historical data from Kraken
        df = fetch_kraken_history(pair)
        
        if df is not None:
            # Load to database
            count = load_prices_to_db(crypto_name, df)
            total_stored += count
        
    logger.info("\n" + "="*70)
    logger.info(f"✅ COMPLETE: Stored {total_stored} total price records")
    logger.info("="*70)
    
    # Verify
    logger.info("\n📊 Verifying data...")
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
            logger.info(f"   Total records in database: {result}")
    except Exception as e:
        logger.error(f"Verification failed: {e}")


if __name__ == "__main__":
    main()
