"""
7-Day Bitcoin Model V2 Validation - Simple Manual Runner
Run daily predictions manually in PowerShell

Usage:
    # Run a single prediction now
    python run_prediction_manual.py
    
    # Run predictions for 7 days (interactive)
    python run_prediction_manual.py --interactive
    
    # Check actual prices and update errors
    python run_prediction_manual.py --check-prices
    
    # Generate validation report
    python run_prediction_manual.py --report
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json

# Add directories to path
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
        logging.FileHandler('logs/predictions_manual.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
Path('logs').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)
Path('data/validation').mkdir(parents=True, exist_ok=True)

# Validation tracking file
VALIDATION_DB = Path('data/validation/predictions_7day.json')


def load_validation_db():
    """Load existing predictions from validation database."""
    if VALIDATION_DB.exists():
        try:
            return json.loads(VALIDATION_DB.read_text(encoding='utf-8'))
        except Exception as e:
            logger.warning(f"Could not load validation DB: {e}")
            return {'predictions': [], 'start_date': None}
    return {'predictions': [], 'start_date': None}


def save_validation_db(data):
    """Save predictions to validation database."""
    try:
        VALIDATION_DB.write_text(json.dumps(data, indent=2), encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to save validation DB: {e}")


def run_single_prediction():
    """
    Run a single prediction cycle.
    """
    logger.info("\n" + "=" * 80)
    logger.info(f"BITCOIN PREDICTION CYCLE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 80)
    
    try:
        # Initialize service
        service = PredictionServiceV2(model_dir='models', crypto='bitcoin')
        
        # Load model
        logger.info("Loading model artifacts...")
        if not service.load_model_artifacts():
            logger.error("❌ Failed to load model artifacts")
            return False
        logger.info("✅ Model loaded (R² = {:.4f})".format(service.metadata.get('test_r2', 0)))
        
        # Fetch latest features
        logger.info("Fetching latest Bitcoin features...")
        if not service.fetch_latest_features():
            logger.error("❌ Failed to fetch latest features")
            return False
        logger.info(f"✅ Latest data: {service.latest_timestamp.date()}, Close: ${service.latest_features['close']:.2f}")
        
        # Prepare features
        logger.info("Preparing features (27 technical indicators)...")
        X_scaled = service.prepare_features()
        if X_scaled is None:
            logger.error("❌ Failed to prepare features")
            return False
        logger.info("✅ Features prepared and scaled")
        
        # Make prediction
        logger.info("Generating next-day price prediction...")
        predicted_price = service.make_prediction(X_scaled)
        if predicted_price is None:
            logger.error("❌ Failed to generate prediction")
            return False
        
        # Display prediction
        current_price = service.latest_features['close']
        expected_change = ((predicted_price / current_price) - 1) * 100
        logger.info("")
        logger.info("📊 PREDICTION RESULTS:")
        logger.info(f"  Current price (today):        ${current_price:>12.2f}")
        logger.info(f"  Predicted close (tomorrow):   ${predicted_price:>12.2f}")
        logger.info(f"  Expected change:              {expected_change:>+12.2f}%")
        logger.info(f"  95% Confidence interval:      [${service.prediction['ci_lower']:.2f}, ${service.prediction['ci_upper']:.2f}]")
        logger.info(f"  Prediction date:              {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"  Target date:                  {service.prediction['predicted_timestamp'].strftime('%Y-%m-%d')}")
        logger.info("")
        
        # Store in database
        logger.info("Storing prediction in database...")
        if not service.store_prediction():
            logger.error("❌ Failed to store prediction")
            return False
        logger.info("✅ Prediction stored in bitcoin_predictions_v2 table")
        
        # Save to validation DB
        validation_db = load_validation_db()
        if not validation_db['start_date']:
            validation_db['start_date'] = datetime.now().isoformat()
        
        pred_record = {
            'day': len(validation_db['predictions']) + 1,
            'prediction_date': datetime.now().isoformat(),
            'target_date': service.prediction['predicted_timestamp'].isoformat(),
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'expected_change_pct': float(expected_change),
            'ci_lower': float(service.prediction['ci_lower']),
            'ci_upper': float(service.prediction['ci_upper']),
            'status': 'pending_confirmation',
            'actual_price': None,
            'error_pct': None
        }
        
        validation_db['predictions'].append(pred_record)
        save_validation_db(validation_db)
        logger.info(f"✅ Prediction #{pred_record['day']} saved to validation database")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ PREDICTION CYCLE COMPLETE")
        logger.info("=" * 80)
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Exception during prediction: {e}", exc_info=True)
        return False


def check_and_confirm_prices():
    """
    Check actual prices for pending predictions and calculate errors.
    """
    logger.info("\n" + "=" * 80)
    logger.info(f"CHECKING ACTUAL PRICES: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 80)
    
    try:
        validation_db = load_validation_db()
        pending = [p for p in validation_db['predictions'] if p['status'] == 'pending_confirmation']
        
        if not pending:
            logger.info("No pending predictions to confirm")
            return
        
        logger.info(f"Found {len(pending)} pending prediction(s)")
        
        for pred in pending:
            target_date = datetime.fromisoformat(pred['target_date']).date()
            logger.info(f"\nChecking actual price for {target_date}...")
            
            # Query computed_features for actual close
            query = text(f"""
                SELECT close, high, low, open, volume 
                FROM computed_features 
                WHERE DATE(timestamp) = '{target_date}' 
                AND cryptocurrency = 'bitcoin'
                LIMIT 1
            """)
            
            try:
                with engine.connect() as conn:
                    result = conn.execute(query)
                    row = result.fetchone()
                    
                    if row:
                        actual_price = float(row[0])
                        predicted_price = pred['predicted_price']
                        current_price = pred['current_price']
                        
                        # Calculate error
                        error_pct = abs(actual_price - predicted_price) / actual_price * 100
                        
                        # Check direction
                        pred_direction = predicted_price > current_price
                        actual_direction = actual_price > current_price
                        direction_correct = pred_direction == actual_direction
                        
                        # Update record
                        pred['actual_price'] = actual_price
                        pred['error_pct'] = error_pct
                        pred['direction_correct'] = direction_correct
                        pred['status'] = 'confirmed'
                        
                        # Log result
                        logger.info(f"  Predicted: ${predicted_price:.2f}")
                        logger.info(f"  Actual:    ${actual_price:.2f}")
                        logger.info(f"  Error:     {error_pct:.2f}%")
                        logger.info(f"  Direction: {'✅ CORRECT' if direction_correct else '❌ WRONG'}")
                    else:
                        logger.info(f"  No data yet for {target_date} (market may not have closed)")
            
            except Exception as e:
                logger.error(f"Error querying price for {target_date}: {e}")
        
        # Save updated database
        save_validation_db(validation_db)
        
        # Print summary
        confirmed = [p for p in validation_db['predictions'] if p['status'] == 'confirmed']
        if confirmed:
            errors = [p['error_pct'] for p in confirmed]
            directions = [p['direction_correct'] for p in confirmed]
            
            logger.info("\n" + "-" * 80)
            logger.info("CONFIRMATION SUMMARY:")
            logger.info(f"  Predictions confirmed:     {len(confirmed)}")
            logger.info(f"  Average error:             {sum(errors)/len(errors):.2f}%")
            logger.info(f"  Directional accuracy:      {sum(directions)/len(directions)*100:.1f}%")
            logger.info(f"  Min error:                 {min(errors):.2f}%")
            logger.info(f"  Max error:                 {max(errors):.2f}%")
            logger.info("-" * 80)
    
    except Exception as e:
        logger.error(f"❌ Exception during price check: {e}", exc_info=True)


def generate_report():
    """Generate validation report."""
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING VALIDATION REPORT")
    logger.info("=" * 80)
    
    try:
        validation_db = load_validation_db()
        predictions = validation_db['predictions']
        confirmed = [p for p in predictions if p['status'] == 'confirmed']
        pending = [p for p in predictions if p['status'] == 'pending_confirmation']
        
        # Calculate stats
        if confirmed:
            errors = [p['error_pct'] for p in confirmed]
            directions = [p['direction_correct'] for p in confirmed]
            avg_error = sum(errors) / len(errors)
            directional_accuracy = sum(directions) / len(directions) * 100
        else:
            avg_error = None
            directional_accuracy = None
        
        # Generate report
        report = f"""# Bitcoin Model V2 - 7-Day Validation Report

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Validation Start:** {validation_db.get('start_date', 'Unknown')}

## Summary

- **Total Predictions:** {len(predictions)}
- **Confirmed (with actuals):** {len(confirmed)}
- **Pending (awaiting actuals):** {len(pending)}

## Performance Metrics

"""
        
        if confirmed:
            errors = [p['error_pct'] for p in confirmed]
            directions = [p['direction_correct'] for p in confirmed]
            report += f"""- **Average Absolute Error:** {avg_error:.2f}%
- **Mean Absolute Percentage Error (MAPE):** {avg_error:.2f}%
- **Directional Accuracy:** {directional_accuracy:.1f}%
- **Min Error:** {min(errors):.2f}%
- **Max Error:** {max(errors):.2f}%
- **Std Dev Error:** {(sum((e - avg_error)**2 for e in errors) / len(errors))**0.5:.2f}%

## Validation Status

"""
            if avg_error < 5 and directional_accuracy > 75:
                report += "✅ **PASS** - Model meets validation criteria\n"
                report += f"   - MAE: {avg_error:.2f}% < 5%\n"
                report += f"   - Directional Accuracy: {directional_accuracy:.1f}% > 75%\n"
            elif avg_error < 3:
                report += "⚠️  **WARNING** - Low error but lower directional accuracy\n"
                report += f"   - MAE: {avg_error:.2f}% (excellent)\n"
                report += f"   - Directional Accuracy: {directional_accuracy:.1f}% (needs improvement)\n"
            else:
                report += "❌ **REVIEW NEEDED** - Model performance below threshold\n"
                report += f"   - MAE: {avg_error:.2f}% (target < 5%)\n"
                report += f"   - Directional Accuracy: {directional_accuracy:.1f}% (target > 75%)\n"
        else:
            report += "🔄 **Awaiting actual price data** - No confirmed predictions yet\n"
        
        # Add detailed predictions
        report += "\n## Detailed Predictions\n"
        for pred in predictions:
            report += f"\n### Day {pred['day']}: {datetime.fromisoformat(pred['target_date']).date()}\n"
            report += f"- **Prediction Date:** {datetime.fromisoformat(pred['prediction_date']).strftime('%Y-%m-%d %H:%M UTC')}\n"
            report += f"- **Current Price:** ${pred['current_price']:.2f}\n"
            report += f"- **Predicted Price:** ${pred['predicted_price']:.2f}\n"
            report += f"- **Expected Change:** {pred['expected_change_pct']:+.2f}%\n"
            
            if pred['status'] == 'confirmed':
                report += f"- **Actual Price:** ${pred['actual_price']:.2f}\n"
                report += f"- **Error:** {pred['error_pct']:.2f}%\n"
                report += f"- **Direction:** {'✅ CORRECT' if pred['direction_correct'] else '❌ WRONG'}\n"
            else:
                report += f"- **Status:** {pred['status']}\n"
            
            report += f"- **95% CI:** [${pred['ci_lower']:.2f}, ${pred['ci_upper']:.2f}]\n"
        
        # Write report
        report_file = Path('reports/VALIDATION_7DAY.md')
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report, encoding='utf-8')
        
        logger.info(f"✅ Report written to: {report_file}")
        logger.info("\nReport Preview:")
        logger.info(report)
    
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)


def print_status():
    """Print current validation status."""
    validation_db = load_validation_db()
    predictions = validation_db['predictions']
    confirmed = [p for p in predictions if p['status'] == 'confirmed']
    
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION STATUS")
    logger.info("=" * 80)
    logger.info(f"Total predictions: {len(predictions)}")
    logger.info(f"Confirmed: {len(confirmed)}")
    logger.info(f"Pending: {len(predictions) - len(confirmed)}")
    
    if confirmed:
        errors = [p['error_pct'] for p in confirmed]
        directions = [p['direction_correct'] for p in confirmed]
        logger.info(f"\nPerformance:")
        logger.info(f"  Avg Error:            {sum(errors)/len(errors):.2f}%")
        logger.info(f"  Directional Accuracy: {sum(directions)/len(directions)*100:.1f}%")
    
    if predictions:
        latest = predictions[-1]
        logger.info(f"\nLatest Prediction:")
        logger.info(f"  Date:     {datetime.fromisoformat(latest['target_date']).date()}")
        logger.info(f"  Predicted: ${latest['predicted_price']:.2f} (expected {latest['expected_change_pct']:+.2f}%)")
        logger.info(f"  Status:   {latest['status']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == '--check-prices':
            check_and_confirm_prices()
        elif cmd == '--report':
            generate_report()
        elif cmd == '--status':
            print_status()
        else:
            print(__doc__)
    else:
        # Default: run single prediction
        run_single_prediction()
