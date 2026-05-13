#!/usr/bin/env python
"""
Check latest prices and features for each cryptocurrency
Shows:
1. If features are computed for all cryptos
2. Latest finalized date/price (yesterday's close)
3. Today's forming candle
"""

from Code.data.db_connection import get_connection
import pandas as pd
from datetime import datetime, timezone, timedelta

engine = get_connection()

# Get previous day (yesterday) and today's timestamps
now_utc = datetime.now(timezone.utc)
today_midnight = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_midnight = today_midnight - timedelta(days=1)

# Convert to naive datetime for comparison with DB (which returns naive)
today_midnight_naive = today_midnight.replace(tzinfo=None)
yesterday_midnight_naive = yesterday_midnight.replace(tzinfo=None)

# Get latest prices
price_query = """
WITH latest_data AS (
    SELECT 
        cryptocurrency,
        timestamp,
        close,
        ROW_NUMBER() OVER (PARTITION BY cryptocurrency ORDER BY timestamp DESC) as rn
    FROM prices
)
SELECT cryptocurrency, timestamp, close
FROM latest_data
WHERE rn = 1
ORDER BY cryptocurrency;
"""

# Get date range for each cryptocurrency
date_range_query = """
SELECT 
    cryptocurrency,
    MIN(timestamp) as first_date,
    MAX(timestamp) as last_date,
    COUNT(*) as price_count
FROM prices
GROUP BY cryptocurrency
ORDER BY cryptocurrency;
"""

df_prices = pd.read_sql(price_query, engine)
df_date_ranges = pd.read_sql(date_range_query, engine)

# Get feature status
feature_query = """
SELECT 
    cryptocurrency,
    COUNT(*) as feature_count,
    MAX(timestamp) as latest_feature_date
FROM computed_features
GROUP BY cryptocurrency
ORDER BY cryptocurrency;
"""

try:
    df_features = pd.read_sql(feature_query, engine)
    has_features = True
    feature_status = {row['cryptocurrency']: (row['feature_count'], row['latest_feature_date']) 
                      for _, row in df_features.iterrows()}
except Exception as e:
    has_features = False
    feature_status = {}
    print(f"⚠️ Features table error: {e}\n")

# Create date range lookup
date_range_lookup = {row['cryptocurrency']: (row['first_date'], row['last_date'], row['price_count']) 
                     for _, row in df_date_ranges.iterrows()}

# Get counts
prices_count = len(df_prices)
features_count = len(df_features) if has_features else 0

print("\n" + "="*100)
print("📊 CRYPTOCURRENCY DATA STATUS CHECK")
print("="*100)
print(f"Current UTC time: {now_utc.isoformat()}\n")

# Show feature status
print("✨ FEATURE ENGINEERING STATUS")
print("-" * 100)
if has_features and features_count == prices_count:
    print(f"✅ All {features_count} cryptocurrencies have computed features")
elif has_features:
    print(f"⚠️  Only {features_count}/{prices_count} cryptocurrencies have features")
else:
    print("❌ No computed features found")

print()

# Group by whether timestamp is before or after today's midnight
today_data = df_prices[df_prices['timestamp'] >= today_midnight_naive]
yesterday_data = df_prices[df_prices['timestamp'] < today_midnight_naive]

# Show finalized data (latest that won't change)
if len(yesterday_data) > 0:
    print("✅ LATEST FINALIZED DATA (Won't change)")
    print("-" * 100)
    for _, row in yesterday_data.iterrows():
        crypto = row['cryptocurrency']
        has_feat = "✓" if crypto.lower() in feature_status else "✗"
        first_date, last_date, count = date_range_lookup.get(crypto, (None, None, 0))
        date_range_str = f"{first_date} to {last_date}" if first_date else "N/A"
        print(f"  {has_feat} {crypto:20s} - ${row['close']:12.2f} @ {row['timestamp']}")
        print(f"     └─ Date range: {date_range_str} ({count} records)")
    
    # Find the latest finalized date across all cryptos
    latest_finalized_date = yesterday_data['timestamp'].max()
    latest_finalized_price_avg = yesterday_data['close'].mean()
    print(f"\n  📅 Latest finalized date: {latest_finalized_date}")

if len(today_data) > 0:
    print("\n🔄 TODAY'S FORMING CANDLE (Updates throughout day)")
    print("-" * 100)
    for _, row in today_data.iterrows():
        crypto = row['cryptocurrency']
        has_feat = "✓" if crypto.lower() in feature_status else "✗"
        first_date, last_date, count = date_range_lookup.get(crypto, (None, None, 0))
        date_range_str = f"{first_date} to {last_date}" if first_date else "N/A"
        print(f"  {has_feat} {crypto:20s} - ${row['close']:12.2f} @ {row['timestamp']}")
        print(f"     └─ Date range: {date_range_str} ({count} records)")

# Check for missing data gaps
print("\n🔍 DATA COMPLETENESS CHECK")
print("-" * 100)

missing_query = """
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
SELECT 
    ds.cryptocurrency,
    ds.expected_date
FROM date_series ds
LEFT JOIN existing_dates ed ON ds.cryptocurrency = ed.cryptocurrency AND ds.expected_date = ed.actual_date
WHERE ed.actual_date IS NULL
ORDER BY ds.cryptocurrency, ds.expected_date;
"""

try:
    missing_data = pd.read_sql(missing_query, engine)
    
    if len(missing_data) == 0:
        print("✅ No missing data - All dates are complete!")
    else:
        # Group missing dates by cryptocurrency
        missing_by_crypto = missing_data.groupby('cryptocurrency')['expected_date'].apply(list).to_dict()
        
        print(f"⚠️  Found missing data in {len(missing_by_crypto)} cryptocurrency(ies):\n")
        
        for crypto in sorted(missing_by_crypto.keys()):
            missing_dates = missing_by_crypto[crypto]
            print(f"  {crypto}:")
            print(f"     Missing {len(missing_dates)} day(s)")
            
            # Show first few and last few missing dates
            if len(missing_dates) <= 5:
                for date in missing_dates:
                    print(f"       - {date}")
            else:
                for date in missing_dates[:2]:
                    print(f"       - {date}")
                print(f"       ... ({len(missing_dates) - 4} more missing days)")
                for date in missing_dates[-2:]:
                    print(f"       - {date}")
            print()
        
except Exception as e:
    print(f"❌ Error checking missing data: {e}\n")

print("="*100 + "\n")
