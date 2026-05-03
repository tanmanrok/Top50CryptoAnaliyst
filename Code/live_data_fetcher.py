"""
Live Data Fetcher for Cryptocurrency Prices
Fetches daily OHLCV data from Kraken API and stores in PostgreSQL
Daily candles (1440-min) ensure consistency with Phase 0 training data
"""
import os
import sys
import logging
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Create logs directory BEFORE logging setup
os.makedirs('logs', exist_ok=True)

from db_connection import engine
from kraken_live_fetcher import KrakenLiveFetcher, CRYPTO_PAIRS
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_data_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
FETCH_INTERVAL_HOURS = 24  # Fetch daily (matches training data frequency)
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class LiveDataPipeline:
    """
    Pipeline for fetching live daily cryptocurrency data and storing in PostgreSQL
    Uses 1440-minute (daily) candles for consistency with Phase 0 training
    """
    
    def __init__(self, engine, fetch_interval_hours: int = FETCH_INTERVAL_HOURS):
        """
        Initialize live data pipeline
        
        Args:
            engine: SQLAlchemy database engine
            fetch_interval_hours: Hours between fetch cycles (default: 24 = daily)
        """
        self.engine = engine
        self.fetch_interval_hours = fetch_interval_hours
        self.fetcher = KrakenLiveFetcher()
        self.stats = {
            'total_fetched': 0,
            'total_stored': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'start_time': datetime.now(timezone.utc)
        }
        logger.info(f"✅ LiveDataPipeline initialized (daily candles, {fetch_interval_hours}h interval)")
    
    def fetch_crypto_data(self, crypto_name: str, pair: str) -> dict:
        """
        Fetch latest DAILY OHLCV data for a cryptocurrency
        
        Args:
            crypto_name: Cryptocurrency name (e.g., 'bitcoin')
            pair: Kraken pair code (e.g., 'XXBTZUSD')
            
        Returns:
            Dictionary with candle data or None if failed
        """
        try:
            # Fetch 1440-minute (daily) candle from Kraken
            candle = self.fetcher.get_latest_candle(pair, interval=1440)
            
            if candle is None:
                logger.warning(f"⚠️  Failed to fetch {crypto_name}")
                self.stats['total_errors'] += 1
                return None
            
            # Add cryptocurrency name
            candle['cryptocurrency'] = crypto_name
            
            self.stats['total_fetched'] += 1
            logger.info(f"✅ {crypto_name:20s} @ {candle['timestamp']} - ${candle['close']:12.2f}")
            
            return candle
            
        except Exception as e:
            logger.error(f"❌ Error fetching {crypto_name}: {e}")
            self.stats['total_errors'] += 1
            return None
    
    def store_price_data(self, candle: dict) -> bool:
        """
        Insert price record into PostgreSQL prices table
        
        Args:
            candle: Dictionary with candle data
            
        Returns:
            True if successful or duplicate, False if error
        """
        attempt = 0
        
        while attempt < MAX_RETRIES:
            try:
                with self.engine.begin() as conn:
                    # Use INSERT ON CONFLICT to handle duplicates gracefully
                    query = text("""
                        INSERT INTO prices 
                        (cryptocurrency, timestamp, open, high, low, close, volume)
                        VALUES 
                        (:cryptocurrency, :timestamp, :open, :high, :low, :close, :volume)
                        ON CONFLICT (cryptocurrency, timestamp) DO UPDATE
                        SET open = :open, high = :high, low = :low, close = :close, volume = :volume
                    """)
                    
                    conn.execute(query, {
                        'cryptocurrency': candle['cryptocurrency'],
                        'timestamp': candle['timestamp'],
                        'open': float(candle['open']),
                        'high': float(candle['high']),
                        'low': float(candle['low']),
                        'close': float(candle['close']),
                        'volume': float(candle['volume']),
                    })
                
                self.stats['total_stored'] += 1
                return True
                
            except Exception as e:
                attempt += 1
                error_str = str(e).lower()
                
                # Check if it's a duplicate key error
                if 'unique' in error_str or 'duplicate' in error_str or 'conflict' in error_str:
                    logger.debug(f"ℹ️  Duplicate or existing record: {candle['cryptocurrency']} @ {candle['timestamp']}")
                    self.stats['total_duplicates'] += 1
                    return True
                
                if attempt < MAX_RETRIES:
                    logger.warning(f"⚠️  Insert failed (attempt {attempt}/{MAX_RETRIES}), retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"❌ Failed to insert {candle['cryptocurrency']} after {MAX_RETRIES} attempts: {e}")
                    self.stats['total_errors'] += 1
                    return False
        
        return False
    
    def fetch_all_cryptos(self) -> int:
        """
        Fetch latest DAILY data for all cryptocurrencies
        
        Returns:
            Number of successful fetches
        """
        successful = 0
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 Daily Fetch Cycle at {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"{'='*70}")
        
        for crypto_name, pair in CRYPTO_PAIRS.items():
            candle = self.fetch_crypto_data(crypto_name, pair)
            
            if candle:
                if self.store_price_data(candle):
                    successful += 1
                
                # Respect rate limit between requests
                time.sleep(0.1)
        
        logger.info(f"{'='*70}")
        logger.info(f"✅ Daily cycle complete: {successful}/{len(CRYPTO_PAIRS)} successful")
        logger.info(f"{'='*70}\n")
        
        return successful
    
    def verify_data(self) -> None:
        """Verify that data was inserted correctly"""
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM prices"))
                total = result.scalar()
                
                latest = conn.execute(text("""
                    SELECT cryptocurrency, MAX(timestamp), COUNT(*) 
                    FROM prices 
                    GROUP BY cryptocurrency 
                    ORDER BY cryptocurrency
                """)).fetchall()
            
            logger.info(f"📊 Database verification:")
            logger.info(f"   Total records: {total}")
            logger.info(f"   Latest by crypto:")
            for crypto, ts, count in latest:
                logger.info(f"      {crypto:20s} - {count:5d} records, latest: {ts}")
        
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
    
    def calculate_next_utc_midnight(self) -> datetime:
        """
        Calculate time until next UTC midnight (when Kraken publishes new daily candles)
        
        Returns:
            datetime object for next UTC midnight
        """
        now = datetime.now(timezone.utc)
        # Next midnight is tomorrow at 00:00:00 UTC
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return next_midnight
    
    def run_continuous(self) -> None:
        """
        Run the pipeline continuously (24/7)
        Fetches daily data at UTC midnight (when Kraken publishes new daily candles)
        Schedules based on UTC midnight, not relative to start time
        """
        logger.info("🚀 Starting continuous daily data pipeline...")
        logger.info(f"   Fetch trigger: UTC midnight (when Kraken publishes daily candles)")
        logger.info(f"   Data frequency: Daily candles (1440-min)")
        logger.info(f"   Cryptos tracked: {len(CRYPTO_PAIRS)}")
        logger.info("   Press Ctrl+C to stop\n")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                
                # Calculate time until next UTC midnight
                next_midnight = self.calculate_next_utc_midnight()
                now = datetime.now(timezone.utc)
                sleep_seconds = (next_midnight - now).total_seconds()
                
                logger.info(f"⏳ Waiting for next daily candle at UTC midnight...")
                logger.info(f"   Current time: {now.isoformat()}")
                logger.info(f"   Next fetch: {next_midnight.isoformat()}")
                logger.info(f"   Sleeping for {sleep_seconds/3600:.2f} hours\n")
                
                # Sleep until next midnight
                time.sleep(sleep_seconds)
                
                # Fetch all cryptos (now that new candles are available)
                logger.info(f"🌙 UTC midnight reached! Fetching new daily candles...\n")
                start_time = time.time()
                
                self.fetch_all_cryptos()
                
                # Verify insertion
                self.verify_data()
                
                # Calculate runtime
                elapsed = time.time() - start_time
                logger.info(f"✅ Cycle {cycle} completed in {elapsed:.1f}s\n")
        
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Stopping pipeline by user request...")
            self.print_statistics()
        
        except Exception as e:
            logger.error(f"❌ Fatal error in pipeline: {e}")
            self.print_statistics()
            raise
        
        finally:
            self.cleanup()
    
    def run_once(self) -> None:
        """
        Fetch data once and exit (useful for testing/cron)
        Shows when the next automatic fetch will occur
        """
        logger.info("🚀 Running single daily fetch cycle...")
        self.fetch_all_cryptos()
        self.verify_data()
        self.print_statistics()
        
        # Show next scheduled fetch time
        next_midnight = self.calculate_next_utc_midnight()
        now = datetime.now(timezone.utc)
        sleep_seconds = (next_midnight - now).total_seconds()
        
        logger.info(f"\n📅 NEXT SCHEDULED FETCH (UTC midnight):")
        logger.info(f"   Current time: {now.isoformat()}")
        logger.info(f"   Next fetch:  {next_midnight.isoformat()}")
        logger.info(f"   In:          {sleep_seconds/3600:.2f} hours\n")
        
        self.cleanup()
    
    def print_statistics(self) -> None:
        """Print pipeline statistics"""
        runtime = datetime.now(timezone.utc) - self.stats['start_time']
        
        logger.info("\n" + "="*70)
        logger.info("📊 PIPELINE STATISTICS")
        logger.info("="*70)
        logger.info(f"Total fetched:      {self.stats['total_fetched']}")
        logger.info(f"Total stored:       {self.stats['total_stored']}")
        logger.info(f"Total duplicates:   {self.stats['total_duplicates']}")
        logger.info(f"Total errors:       {self.stats['total_errors']}")
        logger.info(f"Runtime:            {runtime}")
        
        total_attempts = self.stats['total_fetched'] + self.stats['total_errors']
        if total_attempts > 0:
            success_rate = (self.stats['total_fetched'] / total_attempts) * 100
            logger.info(f"Success rate:       {success_rate:.1f}%")
        
        logger.info("="*70 + "\n")
    
    def cleanup(self) -> None:
        """Close connections and cleanup"""
        logger.info("🧹 Cleaning up...")
        self.fetcher.close()
        logger.info("✅ Pipeline closed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Live cryptocurrency daily data fetching pipeline'
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'continuous'],
        default='continuous',
        help='Run mode: once (single daily fetch) or continuous (24/7)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=FETCH_INTERVAL_HOURS,
        help=f'Fetch interval in hours (default: {FETCH_INTERVAL_HOURS})'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = LiveDataPipeline(engine, fetch_interval_hours=args.interval)
        
        # Run in selected mode
        if args.mode == 'once':
            pipeline.run_once()
        else:
            pipeline.run_continuous()
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
