from Code.data.db_connection import engine
from sqlalchemy import text

with engine.begin() as conn:
    # Get the count of May 9 predictions
    result = conn.execute(text("SELECT COUNT(*) FROM bitcoin_predictions_v2 WHERE DATE(target_date) = '2026-05-09'"))
    count = result.scalar()
    print(f'Found {count} predictions for May 9')
    
    # Keep only the first one (lowest ID), delete the rest
    conn.execute(text("""
        DELETE FROM bitcoin_predictions_v2 
        WHERE DATE(target_date) = '2026-05-09' 
        AND id NOT IN (
            SELECT MIN(id) FROM bitcoin_predictions_v2 
            WHERE DATE(target_date) = '2026-05-09'
        )
    """))
    
    # Verify
    result = conn.execute(text("SELECT COUNT(*) FROM bitcoin_predictions_v2 WHERE DATE(target_date) = '2026-05-09'"))
    remaining = result.scalar()
    print(f'After cleanup: {remaining} prediction for May 9')
    print("✅ Duplicates removed!")
