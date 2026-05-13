"""
7-Day Bitcoin Model V2 Validation Runner
Runs daily predictions and tracks actual prices to validate model performance.

Usage:
    python run_7day_validation.py

This script will:
1. Run daily at market close (4 PM ET)
2. Generate next-day price prediction
3. Store prediction in database
4. Wait for market close next day
5. Fetch actual close price and calculate error
6. Log performance to validation report
"""

import sys
from pathlib import Path
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import schedule
import json

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'Code'))

from Code.models.predict_v2 import PredictionServiceV2
from data.db_connection import engine
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validation_7day.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)


class ValidationRunner:
    """Manages 7-day validation period with daily predictions and error tracking."""
    
    def __init__(self):
        """Initialize validation runner."""
        self.service = PredictionServiceV2(model_dir='models', crypto='bitcoin')
        self.engine = engine
        self.start_time = datetime.now()
        self.predictions = []
        self.report_file = Path('reports/VALIDATION_7DAY.md')
        
        # ET timezone times (4 PM = 20:00 UTC - approximately)
        # Adjust for your timezone: 4 PM ET = 20:00 UTC (winter) or 21:00 UTC (summer)
        self.prediction_time = "20:00"  # UTC time
        self.market_close_et = "16:00"  # 4 PM ET
        
        logger.info("=" * 80)
        logger.info("7-DAY BITCOIN MODEL V2 VALIDATION RUNNER STARTED")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.start_time}")
        logger.info(f"Daily prediction schedule: {self.market_close_et} ET ({self.prediction_time} UTC)")
        logger.info("")
    
    def run_prediction(self):
        """Run single prediction cycle."""
        logger.info("\n" + "=" * 80)
        logger.info(f"PREDICTION CYCLE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 80)
        
        try:
            # Initialize service and load model
            if not self.service.load_model_artifacts():
                logger.error("❌ Failed to load model artifacts")
                return False
            
            # Fetch latest features
            if not self.service.fetch_latest_features():
                logger.error("❌ Failed to fetch latest features")
                return False
            
            logger.info(f"Latest data timestamp: {self.service.latest_timestamp}")
            logger.info(f"Latest close price: ${self.service.latest_features['close']:.2f}")
            
            # Prepare features
            X_scaled = self.service.prepare_features()
            if X_scaled is None:
                logger.error("❌ Failed to prepare features")
                return False
            
            # Make prediction
            predicted_price = self.service.make_prediction(X_scaled)
            if predicted_price is None:
                logger.error("❌ Failed to generate prediction")
                return False
            
            # Store prediction
            if not self.service.store_prediction():
                logger.error("❌ Failed to store prediction")
                return False
            
            logger.info("✅ Prediction stored successfully")
            
            # Log prediction
            pred_record = {
                'prediction_date': datetime.now().isoformat(),
                'target_date': self.service.prediction['predicted_timestamp'].isoformat(),
                'predicted_price': float(self.service.prediction['predicted_price']),
                'ci_lower': float(self.service.prediction['ci_lower']),
                'ci_upper': float(self.service.prediction['ci_upper']),
                'current_price': float(self.service.latest_features['close']),
                'expected_change_pct': float(((predicted_price / self.service.latest_features['close']) - 1) * 100),
            }
            self.predictions.append(pred_record)
            
            # Schedule check for actual price tomorrow
            self._schedule_price_check(pred_record['target_date'])
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Exception during prediction: {e}", exc_info=True)
            return False
    
    def check_and_store_actual_price(self, target_date: str):
        """
        Fetch actual close price for target date and calculate error.
        
        Args:
            target_date: ISO format date string of prediction target
        """
        logger.info("\n" + "-" * 80)
        logger.info(f"CHECKING ACTUAL PRICE FOR: {target_date}")
        logger.info("-" * 80)
        
        try:
            target_dt = datetime.fromisoformat(target_date).date()
            
            # Query computed_features for actual close price on target date
            query = text(f"""
                SELECT close FROM computed_features 
                WHERE DATE(timestamp) = '{target_dt}' 
                AND cryptocurrency = 'bitcoin'
                LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query)
                row = result.fetchone()
                
                if row:
                    actual_price = float(row[0])
                    
                    # Find matching prediction
                    matching_pred = None
                    for pred in self.predictions:
                        if pred['target_date'] == target_date:
                            matching_pred = pred
                            break
                    
                    if matching_pred:
                        predicted_price = matching_pred['predicted_price']
                        error = abs(actual_price - predicted_price) / actual_price * 100
                        direction_correct = (predicted_price > matching_pred['current_price'] and 
                                            actual_price > matching_pred['current_price']) or \
                                          (predicted_price < matching_pred['current_price'] and 
                                           actual_price < matching_pred['current_price'])
                        
                        logger.info(f"Predicted price: ${predicted_price:.2f}")
                        logger.info(f"Actual price:    ${actual_price:.2f}")
                        logger.info(f"Absolute error:  {error:.2f}%")
                        logger.info(f"Direction:       {'✅ CORRECT' if direction_correct else '❌ WRONG'}")
                        
                        # Update prediction in database
                        self._update_prediction_with_actual(target_dt, actual_price, error)
                        
                        # Update local record
                        matching_pred['actual_price'] = actual_price
                        matching_pred['error_pct'] = error
                        matching_pred['direction_correct'] = direction_correct
                    else:
                        logger.warning(f"No matching prediction found for {target_date}")
                else:
                    logger.warning(f"No actual price found for {target_dt}")
        
        except Exception as e:
            logger.error(f"Error checking actual price: {e}", exc_info=True)
    
    def _schedule_price_check(self, target_date_iso: str):
        """
        Schedule a price check for tomorrow (approximately).
        
        Args:
            target_date_iso: ISO format datetime string
        """
        logger.info(f"Scheduled price check for: {target_date_iso}")
        # In production, this would use a task scheduler or queue system
        # For now, we'll log when manual check should occur
    
    def _update_prediction_with_actual(self, target_date, actual_price: float, error_pct: float):
        """Update prediction record with actual price and error."""
        try:
            query = text(f"""
                UPDATE bitcoin_predictions_v2 
                SET actual_price = {actual_price},
                    prediction_error = {error_pct},
                    status = 'confirmed'
                WHERE DATE(target_date) = '{target_date}'
                AND status = 'pending'
            """)
            
            with self.engine.begin() as conn:
                conn.execute(query)
                logger.info("✓ Updated prediction record with actual price")
        except Exception as e:
            logger.error(f"Failed to update prediction: {e}")
    
    def generate_report(self):
        """Generate 7-day validation report."""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING 7-DAY VALIDATION REPORT")
        logger.info("=" * 80)
        
        try:
            # Ensure reports directory exists
            Path('reports').mkdir(exist_ok=True)
            
            # Calculate statistics
            predictions_with_actuals = [p for p in self.predictions if 'actual_price' in p]
            
            if predictions_with_actuals:
                errors = [p['error_pct'] for p in predictions_with_actuals]
                directions = [p['direction_correct'] for p in predictions_with_actuals]
                
                avg_error = sum(errors) / len(errors)
                directional_accuracy = sum(directions) / len(directions) * 100
                mae = avg_error  # Mean absolute error in %
                mape = mae  # Same as MAE in this case
            else:
                avg_error = None
                directional_accuracy = None
                mae = None
                mape = None
            
            # Build report
            report = f"""# 7-Day Bitcoin Model V2 Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Validation Period:** {self.start_time.date()} to {datetime.now().date()}

## Summary Statistics

- **Predictions Made:** {len(self.predictions)}
- **Predictions with Actual Data:** {len(predictions_with_actuals)}
- **Average Absolute Error:** {avg_error:.2f}% (if available)
- **Directional Accuracy:** {directional_accuracy:.1f}% (if available)

## Performance Thresholds

- ✅ PASS: MAE < 5% AND Directional Accuracy > 75%
- ⚠️  WARNING: MAE < 3% but lower directional accuracy
- ❌ FAIL: MAE > 5% OR Directional Accuracy < 75%

**Current Status:** {'Under Review' if len(predictions_with_actuals) < 5 else 'See Results Below'}

## Detailed Predictions

"""
            # Add prediction details
            for i, pred in enumerate(self.predictions, 1):
                report += f"\n### Prediction #{i}\n"
                report += f"- **Date Made:** {pred['prediction_date']}\n"
                report += f"- **Target Date:** {pred['target_date']}\n"
                report += f"- **Current Price:** ${pred['current_price']:.2f}\n"
                report += f"- **Predicted Price:** ${pred['predicted_price']:.2f}\n"
                report += f"- **Expected Change:** {pred['expected_change_pct']:+.2f}%\n"
                
                if 'actual_price' in pred:
                    report += f"- **Actual Price:** ${pred['actual_price']:.2f}\n"
                    report += f"- **Error:** {pred['error_pct']:.2f}%\n"
                    report += f"- **Direction:** {'✅ CORRECT' if pred['direction_correct'] else '❌ WRONG'}\n"
                else:
                    report += f"- **Status:** Awaiting actual price\n"
                
                if 'ci_lower' in pred:
                    report += f"- **95% CI:** [${pred['ci_lower']:.2f}, ${pred['ci_upper']:.2f}]\n"
            
            # Write report
            self.report_file.parent.mkdir(exist_ok=True)
            self.report_file.write_text(report, encoding='utf-8')
            logger.info(f"✓ Report written to: {self.report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
    
    def run(self):
        """Main validation loop."""
        logger.info(f"\nStarting 7-day validation (will run daily at {self.market_close_et} ET)")
        logger.info("To run manually, call: runner.run_prediction()")
        logger.info("To generate report, call: runner.generate_report()")
        logger.info("")
        
        # Schedule daily predictions
        schedule.every().day.at(self.prediction_time).do(self.run_prediction)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            logger.info("\n✓ Validation stopped by user")
            self.generate_report()


def run_single_prediction():
    """Utility to run a single prediction immediately."""
    runner = ValidationRunner()
    success = runner.run_prediction()
    runner.generate_report()
    return success


if __name__ == "__main__":
    # Check if user wants to run a single prediction now
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        logger.info("Running single prediction immediately...")
        run_single_prediction()
    else:
        # Start scheduled validation
        runner = ValidationRunner()
        runner.run()
