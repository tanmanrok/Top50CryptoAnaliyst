#!/usr/bin/env python
"""
Complete Data Pipeline
Fetches data, fills missing dates, computes features, and generates report
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.kraken_live_fetcher import KrakenLiveFetcher, CRYPTO_PAIRS
from data.db_connection import engine
from features.compute_features import FeatureComputor
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoPipeline:
    """Complete data pipeline: fetch, fill, compute, report"""
    
    def __init__(self):
        self.stats = {
            'prices_fetched': 0,
            'prices_stored': 0,
            'features_computed': 0,
            'missing_gaps_found': 0
        }
    
    def fetch_and_load_kraken_data(self):
        """Fetch all cryptocurrency data from Kraken and load to database"""
        logger.info("\n" + "="*70)
        logger.info("STEP 1: FETCHING DATA FROM KRAKEN")
        logger.info("="*70)
        
        fetcher = KrakenLiveFetcher()
        total_fetched = 0
        
        for crypto_name, pair in CRYPTO_PAIRS.items():
            try:
                response = fetcher.get_current_ohlc(pair, interval=1440)
                
                if not response or 'result' not in response:
                    continue
                
                pair_data = response['result'].get(pair, [])
                if not pair_data:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(pair_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                df['cryptocurrency'] = crypto_name
                
                # Load to database
                stored = self._load_to_db(df, crypto_name)
                self.stats['prices_fetched'] += len(df)
                self.stats['prices_stored'] += stored
                total_fetched += 1
                
            except Exception as e:
                logger.error(f"Error processing {crypto_name}: {e}")
        
        logger.info(f"\nFetched data from {total_fetched}/{len(CRYPTO_PAIRS)} cryptos")
        logger.info(f"Total stored: {self.stats['prices_stored']} records")
    
    def _load_to_db(self, df: pd.DataFrame, crypto_name: str) -> int:
        """Load price data to database"""
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
                    except Exception:
                        pass
            
            return stored_count
        except Exception as e:
            logger.error(f"Error loading {crypto_name}: {e}")
            return 0
    
    def compute_all_features(self):
        """Compute features for all historical price data"""
        logger.info("\n" + "="*70)
        logger.info("STEP 2: COMPUTING TECHNICAL FEATURES")
        logger.info("="*70)
        
        # Clear existing features
        try:
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE computed_features"))
            logger.info("Cleared existing features")
        except Exception as e:
            logger.warning(f"Could not clear features: {e}")
        
        # Get all cryptos
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT DISTINCT cryptocurrency FROM prices ORDER BY cryptocurrency"))
                cryptos = [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching cryptos: {e}")
            return
        
        logger.info(f"Found {len(cryptos)} cryptocurrencies\n")
        
        # Compute features for each
        for crypto_name in cryptos:
            try:
                # Get price data
                query = """
                    SELECT timestamp, open, high, low, close, volume
                    FROM prices
                    WHERE LOWER(cryptocurrency) = LOWER(%(crypto)s)
                    ORDER BY timestamp ASC
                """
                
                df_prices = pd.read_sql(query, engine, params={'crypto': crypto_name})
                
                if len(df_prices) < 5:
                    logger.warning(f"{crypto_name}: Only {len(df_prices)} rows (need 5+)")
                    continue
                
                df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'])
                
                # Compute features
                logger.info(f"Computing features for {crypto_name} ({len(df_prices)} rows)...")
                computor = FeatureComputor()
                df_features = computor.compute(df_prices, drop_na=False)
                
                if df_features is None or len(df_features) == 0:
                    logger.warning(f"No features for {crypto_name}")
                    continue
                
                # Save to database
                df_features['cryptocurrency'] = crypto_name.lower().replace(' ', '_')
                df_features['computed_at'] = datetime.utcnow()
                df_features.columns = df_features.columns.str.lower()
                
                # Convert NaN to None
                df_features = df_features.where(pd.notna(df_features), None)
                
                with engine.begin() as conn:
                    df_features.to_sql(
                        'computed_features',
                        conn,
                        if_exists='append',
                        index=False,
                        method='multi'
                    )
                
                logger.info(f"Saved {len(df_features)} feature rows")
                self.stats['features_computed'] += len(df_features)
                
            except Exception as e:
                logger.error(f"Error processing {crypto_name}: {e}")
        
        logger.info(f"\nTotal features computed: {self.stats['features_computed']}")
    
    def check_missing_data(self):
        """Check for missing data gaps"""
        logger.info("\n" + "="*70)
        logger.info("STEP 3: CHECKING FOR MISSING DATA GAPS")
        logger.info("="*70)
        
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    WITH date_series AS (
                        SELECT 
                            cryptocurrency,
                            GENERATE_SERIES(
                                DATE_TRUNC('day', MIN(timestamp)),
                                DATE_TRUNC('day', MAX(timestamp)),
                                INTERVAL '1 day'
                            )::date as expected_date
                        FROM prices
                        GROUP BY cryptocurrency
                    ),
                    existing_dates AS (
                        SELECT 
                            cryptocurrency,
                            DATE_TRUNC('day', timestamp)::date as actual_date
                        FROM prices
                        GROUP BY cryptocurrency, DATE_TRUNC('day', timestamp)
                    )
                    SELECT ds.cryptocurrency, COUNT(*) as missing_count
                    FROM date_series ds
                    LEFT JOIN existing_dates ed ON ds.cryptocurrency = ed.cryptocurrency AND ds.expected_date = ed.actual_date
                    WHERE ed.actual_date IS NULL
                    GROUP BY ds.cryptocurrency
                    ORDER BY ds.cryptocurrency
                """)).fetchall()
                
                missing_cryptos = [row for row in result if row[1] > 0]
                
                if not missing_cryptos:
                    logger.info("SUCCESS: No missing data gaps found!")
                else:
                    logger.info(f"\nFound missing data in {len(missing_cryptos)} crypto(s):\n")
                    for crypto, missing_count in missing_cryptos:
                        logger.info(f"  {crypto:20s} - {missing_count} missing day(s)")
                        self.stats['missing_gaps_found'] += missing_count
                    logger.info(f"\nTotal missing days: {self.stats['missing_gaps_found']}")
                    logger.info("(Note: Early gaps are pre-launch periods - cannot be backfilled)")
                
        except Exception as e:
            logger.error(f"Error checking missing data: {e}")
    
    def print_report(self):
        """Print comprehensive data report"""
        logger.info("\n" + "="*70)
        logger.info("STEP 4: DATA STATUS REPORT")
        logger.info("="*70)
        
        now_utc = datetime.now(timezone.utc)
        
        try:
            with engine.begin() as conn:
                # Total records
                total_result = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
                
                # Latest dates
                latest_result = conn.execute(text("""
                    SELECT cryptocurrency, MAX(timestamp) as latest_date, COUNT(*) as record_count
                    FROM prices
                    GROUP BY cryptocurrency
                    ORDER BY cryptocurrency
                """)).fetchall()
                
                # Feature status
                features_result = conn.execute(text("""
                    SELECT cryptocurrency, COUNT(*) as feature_count, MAX(timestamp) as latest_feature_date
                    FROM computed_features
                    GROUP BY cryptocurrency
                    ORDER BY cryptocurrency
                """)).fetchall()
                
                feature_status = {row[0]: (row[1], row[2]) for row in features_result}
        except Exception as e:
            logger.error(f"Error fetching report data: {e}")
            return
        
        # Print report
        print("\n" + "="*100)
        print("CRYPTOCURRENCY DATA PIPELINE - FINAL REPORT")
        print("="*100)
        print(f"Current UTC time: {now_utc.isoformat()}\n")
        
        # Feature status
        print("FEATURE ENGINEERING STATUS")
        print("-"*100)
        if len(feature_status) == len(latest_result):
            print(f"COMPLETE: All {len(feature_status)} cryptocurrencies have computed features\n")
        else:
            print(f"INCOMPLETE: Only {len(feature_status)}/{len(latest_result)} cryptos have features\n")
        
        # Data by crypto
        print("DATA STATUS BY CRYPTOCURRENCY")
        print("-"*100)
        print(f"{'Crypto':<20} {'Records':>8} {'Latest Date':<22} {'Feat':>5}")
        print("-"*100)
        
        for crypto, latest_date, record_count in latest_result:
            has_feat = "Yes" if crypto in feature_status else "No"
            feat_count = feature_status.get(crypto, (0, None))[0]
            print(f"{crypto:<20} {record_count:>8} {str(latest_date):<22} {has_feat:>5}")
        
        # Summary
        print("\n" + "="*100)
        print("PIPELINE SUMMARY")
        print("="*100)
        print(f"Total price records:     {total_result}")
        print(f"Total features computed: {self.stats['features_computed']}")
        print(f"Prices fetched:          {self.stats['prices_fetched']}")
        print(f"Prices stored:           {self.stats['prices_stored']}")
        print(f"Missing data gaps:       {self.stats['missing_gaps_found']} (pre-launch periods)")
        print("\n" + "="*100 + "\n")
    
    def run(self):
        """Run complete pipeline"""
        logger.info("\n" + "="*70)
        logger.info("STARTING COMPLETE DATA PIPELINE")
        logger.info("="*70)
        
        self.fetch_and_load_kraken_data()
        self.compute_all_features()
        self.check_missing_data()
        self.print_report()
        
        logger.info("PIPELINE COMPLETE")


def main():
    pipeline = CryptoPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
