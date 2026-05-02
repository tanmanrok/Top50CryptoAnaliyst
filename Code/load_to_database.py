"""
Load processed cryptocurrency data into PostgreSQL database
"""
import os
import pandas as pd
from db_connection import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory
PROCESSED_DATA_DIR = 'data/processed'

def load_processed_data():
    """Load all processed CSV files into database"""
    
    # Get all processed CSV files
    csv_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('_processed.csv')]
    
    if not csv_files:
        logger.error(f"No processed CSV files found in {PROCESSED_DATA_DIR}")
        return
    
    logger.info(f"Found {len(csv_files)} processed files to load\n")
    
    total_rows = 0
    failed_cryptos = []
    
    for csv_file in sorted(csv_files):
        crypto_name = csv_file.replace('_processed.csv', '')
        filepath = os.path.join(PROCESSED_DATA_DIR, csv_file)
        
        try:
            logger.info(f"Loading {crypto_name}...")
            
            # Read CSV
            df = pd.read_csv(filepath)
            
            # Ensure correct data types
            df['Date'] = pd.to_datetime(df['Date'])
            df['cryptocurrency'] = crypto_name
            
            # Rename columns to match database schema
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Select only required columns for prices table
            df_prices = df[['cryptocurrency', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Load to database
            df_prices.to_sql('prices', engine, if_exists='append', index=False)
            
            rows_loaded = len(df_prices)
            total_rows += rows_loaded
            logger.info(f"  ✅ Loaded {rows_loaded} rows\n")
            
        except Exception as e:
            logger.error(f"  ❌ Error loading {crypto_name}: {e}\n")
            failed_cryptos.append(crypto_name)
    
    # Summary
    print("=" * 60)
    print(f"LOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(csv_files) - len(failed_cryptos)}/{len(csv_files)}")
    print(f"❌ Failed: {len(failed_cryptos)}/{len(csv_files)}")
    print(f"📊 Total rows loaded: {total_rows}")
    
    if failed_cryptos:
        print(f"\nFailed cryptocurrencies:")
        for crypto in failed_cryptos:
            print(f"  - {crypto}")

if __name__ == "__main__":
    logger.info("Starting data load to PostgreSQL...\n")
    load_processed_data()
    logger.info("Data load complete!")
