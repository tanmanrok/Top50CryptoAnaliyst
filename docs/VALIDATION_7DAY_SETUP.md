## 7-Day Bitcoin Model V2 Validation Setup

This guide shows how to run daily Bitcoin price predictions for 7 days to validate the production model.

### Quick Start (Easiest)

```powershell
# 1. Run a single prediction immediately
python run_prediction_manual.py

# 2. Next day, check actual price and confirm prediction
python run_prediction_manual.py --check-prices

# 3. After 7 days, generate report
python run_prediction_manual.py --report
```

---

### Day-by-Day Example

**Day 1 (Today - May 8, 2026)**
```powershell
# Run at 4 PM ET (market close) to generate tomorrow's prediction
python run_prediction_manual.py

# Output:
# 📊 PREDICTION RESULTS:
#   Current price (today):        $80,250.00
#   Predicted close (tomorrow):   $80,106.13
#   Expected change:              -0.18%
#   95% Confidence interval:      [$80,105.93, $80,106.32]
```

**Day 2 (May 9, 2026)**
```powershell
# After 4 PM ET (after new candle closes), check actual price
python run_prediction_manual.py --check-prices

# Output will show:
#   Predicted: $80,106.13
#   Actual:    $80,XXX.XX
#   Error:     Y.YY%
#   Direction: ✅ CORRECT or ❌ WRONG
```

Repeat daily for 7 days (May 8 - May 14).

**Day 8 (May 15, 2026)**
```powershell
# Generate final report
python run_prediction_manual.py --report

# Shows summary of all 7 days:
# ✅ PASS - Model meets validation criteria
#    - MAE: 2.15% < 5%
#    - Directional Accuracy: 85.7% > 75%
```

---

### Available Commands

```powershell
# Run a single prediction
python run_prediction_manual.py

# Check actual prices for pending predictions
python run_prediction_manual.py --check-prices

# Generate validation report
python run_prediction_manual.py --report

# View current validation status
python run_prediction_manual.py --status

# View help
python run_prediction_manual.py --help
```

---

### Output Files

All validation data is saved to:

- **Predictions JSON:** `data/validation/predictions_7day.json`
- **Prediction Logs:** `logs/predictions_manual.log`
- **Final Report:** `reports/VALIDATION_7DAY.md`
- **Database:** `bitcoin_predictions_v2` table in PostgreSQL

---

### What Gets Logged

Each prediction stores:
- ✅ Predicted price & confidence interval
- ✅ Current Bitcoin price
- ✅ Expected direction & percentage change
- ✅ Prediction timestamp & target date

After 24 hours:
- ✅ Actual close price from market
- ✅ Absolute error percentage
- ✅ Direction correctness (UP/DOWN)

---

### Success Criteria

Model is validated if:
- **Mean Absolute Error (MAE):** < 5%
- **Directional Accuracy:** > 75%

Current model performance (on test data):
- MAE: 2.15%
- Directional: 89.1%
✅ **Expected to PASS validation**

---

### Timezone Notes

- Predictions run at **4 PM ET** (16:00 ET / 20:00-21:00 UTC)
- Adjust `prediction_time` in script if using different timezone
- Bitcoin daily candles close at UTC midnight
- Scripts query database for new candle data

---

### Troubleshooting

**Error: "Failed to load model artifacts"**
- Check that model files exist: `models/v2_final_Ridge_bitcoin.pkl`
- Run: `python Code/models/train_all_models_v2.py` to retrain

**Error: "Failed to fetch latest features"**
- Ensure PostgreSQL is running
- Check that `computed_features` table has recent Bitcoin data
- Run: `python check_latest.py` to verify latest data

**No actual prices found**
- Actual prices need to be fetched after market close
- New daily candles are added to `computed_features` at UTC midnight
- Wait 24 hours after prediction before checking prices

**Database connection errors**
- Verify `.env` file has correct `DATABASE_URL`
- Check PostgreSQL is running: `psql -U postgres`
- Verify credentials in `Code/data/db_connection.py`

---

### Next Steps After Validation

**If PASS (MAE < 5% AND Directional Accuracy > 75%):**
- ✅ Deploy to production
- ✅ Run daily predictions indefinitely
- ✅ Retrain weekly: `python Code/models/retrain_model_v2.py`

**If FAIL:**
- ❌ Analyze why model underperformed
- ❌ Check for data quality issues
- ❌ Consider retraining with more recent data
- ❌ Test alternative models (Phase 3)

---

### Production Setup (After Validation)

For continuous production predictions, you have options:

**Option 1: Windows Task Scheduler (Automatic)**
```
Create scheduled task:
- Program: C:\path\to\python.exe
- Arguments: run_prediction_manual.py
- Schedule: Daily at 4 PM ET
```

**Option 2: PowerShell Script (Keep Window Open)**
```powershell
# Create run_daily.ps1
while($true) {
    python run_prediction_manual.py
    Start-Sleep -Seconds 3600  # Check hourly
}

# Then in PowerShell:
.\run_daily.ps1
```

**Option 3: Docker Container (Production Recommended)**
```bash
docker build -t bitcoin-predictor .
docker run -d --name bitcoin-predictor bitcoin-predictor
```

---

### Questions?

- Check logs: `cat logs/predictions_manual.log`
- View latest predictions: `python run_prediction_manual.py --status`
- Review code: `Code/models/predict_v2.py`
- See detailed report: `reports/VALIDATION_7DAY.md`
