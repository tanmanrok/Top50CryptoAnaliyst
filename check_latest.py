#!/usr/bin/env python
"""
Check latest prices for each cryptocurrency
Shows both:
1. Previous day's finalized candle (closed at UTC midnight)
2. Today's current forming candle
"""

from Code.db_connection import get_connection
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

query = """
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

df = pd.read_sql(query, engine)

print("\n" + "="*80)
print("📊 CRYPTOCURRENCY PRICE CHECK")
print("="*80)
print(f"Current UTC time: {now_utc.isoformat()}\n")

# Group by whether timestamp is before or after today's midnight
today_data = df[df['timestamp'] >= today_midnight_naive]
yesterday_data = df[df['timestamp'] < today_midnight_naive]

if len(yesterday_data) > 0:
    print("✅ PREVIOUS DAY (FINALIZED - Won't change)")
    print("-" * 80)
    for _, row in yesterday_data.iterrows():
        print(f"  {row['cryptocurrency']:20s} - ${row['close']:12.2f} @ {row['timestamp']}")

if len(today_data) > 0:
    print("\n🔄 TODAY (CURRENTLY FORMING - Updates throughout day)")
    print("-" * 80)
    for _, row in today_data.iterrows():
        print(f"  {row['cryptocurrency']:20s} - ${row['close']:12.2f} @ {row['timestamp']}")

print("\n" + "="*80 + "\n")
