"""
Merge backfilled data with existing interim data.
Combines backfilled Kraken data with existing cleaned data, removing duplicates
and keeping the most recent version of each record.
"""

import pandas as pd
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataMerger:
    """Merges backfilled data with existing interim data."""
    
    def __init__(self, backfill_dir: str = 'data/interim/backfilled',
                 interim_dir: str = 'data/interim',
                 output_dir: str = 'data/interim/merged'):
        self.backfill_dir = backfill_dir
        self.interim_dir = interim_dir
        self.output_dir = output_dir
        self.merge_results = {}
    
    def merge_all(self) -> dict:
        """Merge all backfilled files with existing data."""
        backfill_files = sorted(Path(self.backfill_dir).glob('*_backfilled.csv'))
        
        if not backfill_files:
            logger.warning(f"No backfilled CSV files found in {self.backfill_dir}")
            return {}
        
        logger.info(f"Found {len(backfill_files)} backfilled files")
        os.makedirs(self.output_dir, exist_ok=True)
        
        for backfill_file in backfill_files:
            crypto_name = backfill_file.stem.replace('_backfilled', '')
            logger.info(f"\nProcessing {crypto_name}...")
            
            try:
                # Read backfilled data
                df_backfilled = pd.read_csv(backfill_file)
                df_backfilled['timestamp'] = pd.to_datetime(df_backfilled['timestamp'], utc=True)
                # Remove timezone for consistent comparison
                df_backfilled['timestamp'] = df_backfilled['timestamp'].dt.tz_localize(None)
                
                # Look for existing cleaned data
                cleaned_file = Path(self.interim_dir) / f'{crypto_name}_cleaned.csv'
                
                if cleaned_file.exists():
                    logger.info(f"  Found existing cleaned data: {cleaned_file.name}")
                    
                    # Read the cleaned file with original column names
                    df_existing_original = pd.read_csv(cleaned_file)
                    original_columns = df_existing_original.columns.tolist()
                    
                    # Create a mapping of original column names to lowercase for processing
                    column_lower_map = {col.lower(): col for col in original_columns}
                    
                    # Now normalize for processing
                    df_existing = df_existing_original.copy()
                    df_existing.columns = df_existing.columns.str.lower()
                    
                    # Handle different date column names (Date vs timestamp)
                    if 'date' in df_existing.columns:
                        df_existing.rename(columns={'date': 'timestamp'}, inplace=True)
                    
                    # Try to parse timestamp
                    try:
                        df_existing['timestamp'] = pd.to_datetime(df_existing['timestamp'])
                    except Exception as e:
                        logger.warning(f"  Could not parse timestamp in {cleaned_file.name}: {e}")
                        # Skip merge if timestamps don't parse
                        df_merged = df_backfilled[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    else:
                        # Prepare backfilled data with same columns as cleaned
                        df_backfilled_subset = df_backfilled[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
                        
                        # Select only columns from cleaned data
                        df_existing_subset = df_existing[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                        
                        # Merge: combine both datasets
                        df_merged = pd.concat([df_existing_subset, df_backfilled_subset], ignore_index=True)
                        
                        # Remove duplicates, keeping last (most recent)
                        df_merged = df_merged.drop_duplicates(subset=['timestamp'], keep='last')
                        df_merged = df_merged.sort_values('timestamp').reset_index(drop=True)
                        
                        # Restore original column names and order from cleaned data
                        # Apply original casing to current columns
                        restored_columns = []
                        for col in df_merged.columns:
                            # Special case: 'timestamp' should map back to 'Date' if that was the original
                            if col == 'timestamp' and 'date' in column_lower_map:
                                restored_columns.append(column_lower_map['date'])
                            elif col in column_lower_map:
                                restored_columns.append(column_lower_map[col])
                            else:
                                restored_columns.append(col)
                        
                        df_merged.columns = restored_columns
                        
                        # Reorder columns to match original order
                        # Create a mapping of lowercase original names to their current column names
                        current_cols_lower_map = {col.lower(): col for col in df_merged.columns}
                        
                        # Reorder based on original column positions
                        reordered_cols = []
                        for orig_col in original_columns:
                            orig_col_lower = orig_col.lower()
                            if orig_col_lower in current_cols_lower_map:
                                reordered_cols.append(current_cols_lower_map[orig_col_lower])
                        
                        if reordered_cols:  # Only reorder if we found matching columns
                            df_merged = df_merged[reordered_cols]
                        
                        logger.info(f"  Merged: {len(df_existing_subset)} existing + {len(df_backfilled_subset)} backfilled = {len(df_merged)} total")
                else:
                    logger.info(f"  No existing cleaned data found, using backfilled only")
                    df_merged = df_backfilled[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
                    # If no cleaned file, rename to match cleaned format (Date instead of timestamp)
                    df_merged.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
                
                # Save merged data
                output_file = Path(self.output_dir) / f'{crypto_name}_merged.csv'
                df_merged.to_csv(output_file, index=False)
                
                self.merge_results[crypto_name] = {
                    'status': 'SUCCESS',
                    'output_file': str(output_file),
                    'row_count': len(df_merged)
                }
                
                logger.info(f"  Saved to {output_file.name}")
                logger.info(f"  Total rows: {len(df_merged)}")
                
            except Exception as e:
                logger.error(f"  Error merging {crypto_name}: {e}")
                self.merge_results[crypto_name] = {'status': 'FAILED', 'error': str(e)}
        
        return self.merge_results
    
    def generate_merge_summary(self, output_file: str = 'data/interim/merged/MERGE_SUMMARY.md'):
        """Generate a merge summary report."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Data Merge Summary\n\n")
            
            passed = sum(1 for r in self.merge_results.values() if r.get('status') == 'SUCCESS')
            failed = sum(1 for r in self.merge_results.values() if r.get('status') == 'FAILED')
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Datasets:** {len(self.merge_results)}\n")
            f.write(f"- **Successful:** {passed}\n")
            f.write(f"- **Failed:** {failed}\n\n")
            
            f.write("## Detailed Results\n\n")
            
            for crypto_name in sorted(self.merge_results.keys()):
                result = self.merge_results[crypto_name]
                status_icon = "[OK]" if result.get('status') == 'SUCCESS' else "[FAIL]"
                
                f.write(f"### {status_icon} {crypto_name}\n\n")
                
                if result.get('status') == 'SUCCESS':
                    f.write(f"- **Output:** {result.get('output_file')}\n")
                    f.write(f"- **Total Rows:** {result.get('row_count')}\n")
                    f.write(f"- **Date Range:** {result.get('date_range')}\n")
                else:
                    f.write(f"- **Error:** {result.get('error')}\n")
                
                f.write("\n")
        
        logger.info(f"\nMerge summary saved to {output_file}")


if __name__ == '__main__':
    merger = DataMerger()
    results = merger.merge_all()
    merger.generate_merge_summary()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("MERGE SUMMARY")
    logger.info("="*60)
    passed = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
    failed = sum(1 for r in results.values() if r.get('status') == 'FAILED')
    logger.info(f"Successful: {passed}/{len(results)}")
    logger.info(f"Failed: {failed}/{len(results)}")
    logger.info(f"\nMerged files saved to: data/interim/merged/")
