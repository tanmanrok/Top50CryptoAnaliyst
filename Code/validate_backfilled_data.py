"""
Data validation script for backfilled cryptocurrency data.
Checks for data quality issues in the backfilled CSV files.
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataValidator:
    """Validates backfilled cryptocurrency data."""
    
    def __init__(self, backfill_dir: str = 'data/interim/backfilled'):
        self.backfill_dir = backfill_dir
        self.validation_results = {}
    
    def validate_all(self) -> dict:
        """Validate all CSV files in backfill directory."""
        csv_files = sorted(Path(self.backfill_dir).glob('*_backfilled.csv'))
        
        if not csv_files:
            logger.warning(f"No backfilled CSV files found in {self.backfill_dir}")
            return {}
        
        logger.info(f"Found {len(csv_files)} backfilled files to validate")
        
        for csv_file in csv_files:
            crypto_name = csv_file.stem.replace('_backfilled', '')
            logger.info(f"\nValidating {crypto_name}...")
            
            try:
                df = pd.read_csv(csv_file)
                self.validation_results[crypto_name] = self._validate_dataframe(df, crypto_name)
            except Exception as e:
                logger.error(f"  Error reading {csv_file}: {e}")
                self.validation_results[crypto_name] = {'status': 'FAILED', 'error': str(e)}
        
        return self.validation_results
    
    def _validate_dataframe(self, df: pd.DataFrame, crypto_name: str) -> dict:
        """Validate a single dataframe."""
        issues = []
        
        # 1. Check for required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
            return {'status': 'FAILED', 'issues': issues}
        
        # Convert timestamp to datetime
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        except Exception as e:
            issues.append(f"Cannot parse timestamp column: {e}")
            return {'status': 'FAILED', 'issues': issues}
        
        # 2. Check for duplicates
        duplicates = df.duplicated(subset=['timestamp']).sum()
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate timestamps")
        
        # 3. Check for missing dates (gaps in daily data)
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        if len(df_sorted) > 1:
            date_diffs = df_sorted['timestamp'].diff().dt.days
            expected_diff = 1  # Daily data should have 1-day gaps
            
            # Allow for weekends/market closures (up to 3 days)
            large_gaps = date_diffs[(date_diffs > 3) & (date_diffs.notna())]
            if len(large_gaps) > 0:
                issues.append(f"Found {len(large_gaps)} gaps larger than 3 days")
                logger.info(f"  Large gaps: {large_gaps.values}")
        
        # 4. Check OHLC relationships
        ohlc_issues = 0
        
        # High should be >= all others
        high_violations = (df['high'] < df['open']).sum() + \
                         (df['high'] < df['close']).sum() + \
                         (df['high'] < df['low']).sum()
        if high_violations > 0:
            issues.append(f"High < other prices in {high_violations} rows")
            ohlc_issues += high_violations
        
        # Low should be <= all others
        low_violations = (df['low'] > df['open']).sum() + \
                        (df['low'] > df['close']).sum() + \
                        (df['low'] > df['high']).sum()
        if low_violations > 0:
            issues.append(f"Low > other prices in {low_violations} rows")
            ohlc_issues += low_violations
        
        # 5. Check for negative/zero volumes
        zero_volume = (df['volume'] <= 0).sum()
        if zero_volume > 0:
            issues.append(f"Found {zero_volume} rows with volume <= 0")
        
        # 6. Check for NaN values
        nan_counts = df[required_cols].isna().sum()
        nan_issues = nan_counts[nan_counts > 0]
        if len(nan_issues) > 0:
            issues.append(f"Found NaN values: {nan_issues.to_dict()}")
        
        # 7. Check price ranges (basic sanity check)
        for col in ['open', 'high', 'low', 'close']:
            if (df[col] < 0).any():
                issues.append(f"Found negative prices in {col}")
            if (df[col] > 1_000_000).any():
                issues.append(f"Found extremely high prices in {col} (>1M)")
        
        # Build result
        result = {
            'status': 'PASSED' if not issues else 'FAILED',
            'row_count': len(df),
            'date_range': f"{df_sorted['timestamp'].min().date()} to {df_sorted['timestamp'].max().date()}",
            'volume_stats': {
                'min': float(df['volume'].min()),
                'max': float(df['volume'].max()),
                'mean': float(df['volume'].mean())
            },
            'price_stats': {
                'min': float(df[['open', 'high', 'low', 'close']].min().min()),
                'max': float(df[['open', 'high', 'low', 'close']].max().max())
            },
            'issues': issues if issues else None
        }
        
        # Log results
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Rows: {result['row_count']}")
        logger.info(f"  Date range: {result['date_range']}")
        if issues:
            for issue in issues:
                logger.warning(f"  ⚠️  {issue}")
        else:
            logger.info(f"  ✅ All checks passed!")
        
        return result
    
    def generate_report(self, output_file: str = 'data/interim/backfilled/VALIDATION_REPORT.md'):
        """Generate a validation report."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Data Validation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            passed = sum(1 for r in self.validation_results.values() if r.get('status') == 'PASSED')
            failed = sum(1 for r in self.validation_results.values() if r.get('status') == 'FAILED')
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Datasets:** {len(self.validation_results)}\n")
            f.write(f"- **Passed:** {passed}\n")
            f.write(f"- **Failed:** {failed}\n\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            
            for crypto_name in sorted(self.validation_results.keys()):
                result = self.validation_results[crypto_name]
                status_icon = "✅" if result.get('status') == 'PASSED' else "❌"
                
                f.write(f"### {status_icon} {crypto_name}\n\n")
                f.write(f"**Status:** {result.get('status')}\n\n")
                
                if 'error' in result:
                    f.write(f"**Error:** {result['error']}\n\n")
                else:
                    f.write(f"- **Rows:** {result.get('row_count', 'N/A')}\n")
                    f.write(f"- **Date Range:** {result.get('date_range', 'N/A')}\n")
                    
                    if result.get('volume_stats'):
                        vs = result['volume_stats']
                        f.write(f"- **Volume Range:** {vs['min']:.2f} - {vs['max']:.2f}\n")
                    
                    if result.get('price_stats'):
                        ps = result['price_stats']
                        f.write(f"- **Price Range:** ${ps['min']:.2f} - ${ps['max']:.2f}\n")
                    
                    if result.get('issues'):
                        f.write(f"\n**Issues Found:**\n")
                        for issue in result['issues']:
                            f.write(f"- {issue}\n")
                    else:
                        f.write(f"\n**✅ No issues found**\n")
                
                f.write("\n")
        
        logger.info(f"\nValidation report saved to {output_file}")


if __name__ == '__main__':
    validator = DataValidator()
    results = validator.validate_all()
    validator.generate_report()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    passed = sum(1 for r in results.values() if r.get('status') == 'PASSED')
    failed = sum(1 for r in results.values() if r.get('status') == 'FAILED')
    logger.info(f"Passed: {passed}/{len(results)}")
    logger.info(f"Failed: {failed}/{len(results)}")
