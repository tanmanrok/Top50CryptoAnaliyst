#!/usr/bin/env python
"""Check for missing data gaps without emoji"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_connection import engine
from sqlalchemy import text
import pandas as pd

# Check total records
with engine.begin() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
    print(f"Total price records: {result}\n")
    
    # Check latest dates per crypto
    latest = conn.execute(text("""
        SELECT cryptocurrency, MAX(timestamp) as latest_date, COUNT(*) as record_count
        FROM prices
        GROUP BY cryptocurrency
        ORDER BY cryptocurrency
    """)).fetchall()
    
    print("Latest date per cryptocurrency:")
    for crypto, latest_date, count in latest:
        print(f"  {crypto:20s} - {count:5d} records, latest: {latest_date}")
    
    print("\n" + "="*70)
    print("CHECKING FOR DATA GAPS...")
    print("="*70 + "\n")
    
    # Count missing dates per crypto
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
        print("SUCCESS: No missing data gaps found!\n")
    else:
        print(f"Found missing data in {len(missing_cryptos)} cryptocurrency(ies):\n")
        for crypto, missing_count in missing_cryptos:
            print(f"  {crypto:20s} - {missing_count} missing day(s)")
        print()

print("="*70)
