"""
Simple script to compute and update features in the database.
Run from root directory: python update_features_simple.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'Code'))

from data.db_connection import engine
from features.compute_features import compute_features_from_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting feature update...")
    
    try:
        from sqlalchemy import text
        import pandas as pd
        
        # Compute features for all cryptos
        cryptos = ['bitcoin', 'ethereum', 'solana', 'chainlink', 'litecoin', 
                   'binance_coin', 'avalanche', 'cardano', 'polkadot', 'dogecoin',
                   'ripple', 'maker', 'the_graph', 'injective']
        
        for crypto in cryptos:
            logger.info(f"Computing features for {crypto}...")
            try:
                df_features = compute_features_from_db(engine, crypto)
                if df_features is not None and len(df_features) > 0:
                    # Convert column names to lowercase to match database schema
                    df_features.columns = [col.lower() for col in df_features.columns]
                    
                    # Get max timestamp already in database for this crypto
                    with engine.begin() as conn:
                        result = conn.execute(
                            text("SELECT MAX(timestamp) FROM computed_features WHERE cryptocurrency = :crypto"),
                            {"crypto": crypto}
                        )
                        max_ts = result.scalar()
                    
                    # Only insert NEW rows (after max timestamp)
                    if max_ts is not None:
                        df_new = df_features[df_features['timestamp'] > max_ts]
                    else:
                        df_new = df_features
                    
                    if len(df_new) > 0:
                        df_new['cryptocurrency'] = crypto
                        df_new.to_sql(
                            'computed_features',
                            engine,
                            if_exists='append',
                            index=False
                        )
                        logger.info(f"✅ {crypto}: {len(df_new)} new rows stored")
                    else:
                        logger.info(f"ℹ️  {crypto}: No new data (already up-to-date)")
                else:
                    logger.warning(f"⚠️  {crypto}: No features to store")
            except Exception as e:
                logger.warning(f"⚠️  {crypto}: {e}")
        
        logger.info("✅ Feature update complete!")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
