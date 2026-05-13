"""
Phase F: Initialize Bitcoin Predictions Table
Creates the bitcoin_predictions_v2 table in PostgreSQL for storing Model v2 predictions.
"""

import sys
from pathlib import Path
import logging
from sqlalchemy import MetaData

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_connection import engine
from models.predict_v2 import Base, BitcoinPredictionV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_predictions_table():
    """Create bitcoin_predictions_v2 table if it doesn't exist."""
    logger.info("\n" + "=" * 80)
    logger.info("INITIALIZING BITCOIN PREDICTIONS TABLE")
    logger.info("=" * 80)
    
    try:
        # Create all tables defined in Base
        Base.metadata.create_all(engine)
        
        logger.info("✅ Table created successfully: bitcoin_predictions_v2")
        logger.info("\nTable schema:")
        logger.info("  - id: Integer (primary key)")
        logger.info("  - prediction_date: DateTime (when prediction was made)")
        logger.info("  - target_date: DateTime (what date is being predicted)")
        logger.info("  - predicted_price: Float (next-day close price prediction)")
        logger.info("  - confidence_interval_lower: Float (95% CI lower bound)")
        logger.info("  - confidence_interval_upper: Float (95% CI upper bound)")
        logger.info("  - model_version: String (model identifier)")
        logger.info("  - input_features_hash: String (for traceability)")
        logger.info("  - status: String (pending/confirmed/failed)")
        logger.info("  - actual_price: Float (filled after market close)")
        logger.info("  - prediction_error: Float (|predicted - actual| / actual)")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Initialization complete! Ready to store predictions.")
        logger.info("=" * 80 + "\n")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize table: {e}")
        return False


if __name__ == '__main__':
    success = init_predictions_table()
    sys.exit(0 if success else 1)
