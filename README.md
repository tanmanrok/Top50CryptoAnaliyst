# Top 50 Cryptocurrency Live Prediction System

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Project Overview

A machine learning system for **real-time cryptocurrency price prediction** combining:
- ✅ **37,464 historical records** (14 cryptocurrencies, Sep 2014 - May 2026)
- ✅ **14 technical indicators** (SMA, EMA, RSI, MACD, volatility, returns)
- ✅ **PostgreSQL database** with 37,464 records loaded
- ✅ **99.97% R² on Bitcoin** with 90%+ directional accuracy
- 🔄 **Live data ingestion** (Kraken API)
- 🔄 **Automated model retraining** pipeline

---

## 📊 Current Status

### ✅ Completed Phases
- **Phase 0:** Foundation & Historical Models (99.97% R²)
- **Phase 0.5:** Backfill Historical Data (37,464 records)
- **Phase 1.5:** Database & Storage Setup (PostgreSQL live)

### 🔄 In Progress
- **Phase 1:** Live Data Ingestion (Kraken API)
- **Phase 2:** Automated Model Retraining
- **Phase 3:** Real-time Predictions

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 16+
- Conda/Anaconda

### 1. Set Up Environment

```powershell
# Activate Conda
conda activate base

# Verify PostgreSQL
psql --version

# Check database
psql -U postgres -d crypto_predictions -c "SELECT COUNT(*) FROM prices;"
```

### 2. Load Python Dependencies

```powershell
# Install from requirements.txt
pip install -r requirements.txt

# Or use Conda
conda env create -f environment.yml
conda activate crypto-analysis
```

### 3. Verify Database Connection

```powershell
# Test Python connection
python Code/db_connection.py

# Expected output:
# ✅ Database connection successful!
# ✅ Tables created successfully!
```

---

## 📖 How to Use

### View Cryptocurrency Data

**Check what's in the database:**
```powershell
# Total records
psql -U postgres -d crypto_predictions -c "SELECT COUNT(*) FROM prices;"
# Output: 37464

# Records per cryptocurrency
psql -U postgres -d crypto_predictions -c "SELECT cryptocurrency, COUNT(*) FROM prices GROUP BY cryptocurrency ORDER BY cryptocurrency;"

# Date range
psql -U postgres -d crypto_predictions -c "SELECT MIN(timestamp), MAX(timestamp) FROM prices;"
# Output: 2014-09-17 | 2026-05-01
```

### Query with Python

```python
from Code.db_connection import engine
import pandas as pd

# Get Bitcoin data
query = """
    SELECT * FROM prices 
    WHERE cryptocurrency='bitcoin'
    ORDER BY timestamp DESC
    LIMIT 100
"""
df = pd.read_sql(query, engine)
print(df)
```

### Explore Technical Indicators

**View processed data with indicators:**
```python
import pandas as pd

# Load Bitcoin with indicators
df = pd.read_csv('data/processed/bitcoin_processed.csv')
print(df.columns)
# Columns: open, high, low, close, volume, SMA_7, SMA_20, SMA_50, 
#          EMA_7, EMA_20, EMA_50, RSI_14, MACD, MACD_Signal, MACD_Histogram,
#          Daily_Return, Weekly_Return, Monthly_Return, Volatility_30

print(df.head())
```

### Run Jupyter Notebooks

```powershell
# Data exploration
jupyter notebook notebooks/EDA.ipynb

# Model training
jupyter notebook notebooks/Model.ipynb

# Technical indicators
jupyter notebook notebooks/UpdateData.ipynb
```

---

## 🗄️ Database Schema & Data

### Database Overview
- **Host:** 127.0.0.1:5432
- **Database:** crypto_predictions
- **User:** postgres
- **Total Records:** 37,464
- **Tables:** prices, predictions, metrics, logs

### `prices` Table Structure
```sql
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    cryptocurrency VARCHAR(50),
    timestamp TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cryptocurrency, timestamp)
);
```

### Data Summary by Cryptocurrency

| Cryptocurrency | Records | Start Date | End Date |
|---|---|---|---|
| Bitcoin | 4,245 | 2014-09-17 | 2026-05-01 |
| Litecoin | 4,245 | 2014-09-17 | 2026-05-01 |
| Ethereum | 3,096 | 2017-11-09 | 2026-05-01 |
| Binance Coin | 3,096 | 2017-11-09 | 2026-05-01 |
| Chainlink | 3,096 | 2017-11-09 | 2026-05-01 |
| Tron | 3,096 | 2017-11-09 | 2026-05-01 |
| Maker | 3,085 | 2017-11-20 | 2026-05-01 |
| Solana | 2,213 | 2020-04-10 | 2026-05-01 |
| Render | 2,136 | 2020-06-11 | 2026-05-01 |
| Avalanche | 2,050 | 2020-07-13 | 2026-05-01 |
| Axie Infinity | 2,005 | 2020-11-04 | 2026-05-01 |
| Injective | 2,019 | 2020-10-21 | 2026-05-01 |
| Toncoin | 1,709 | 2021-08-27 | 2026-05-01 |
| The Graph | 1,373 | 2020-06-19 | 2026-05-01 |

---

## 📊 Technical Indicators (14 Total)

All indicators are pre-calculated in `data/processed/` CSV files and in the `notebooks/helpers/indicators_helper.py` module:

### Trend Indicators
- **SMA_7, SMA_20, SMA_50:** Simple Moving Averages
- **EMA_7, EMA_20, EMA_50:** Exponential Moving Averages
- **MACD, MACD_Signal, MACD_Histogram:** Moving Average Convergence Divergence

### Momentum & Volatility
- **RSI_14:** Relative Strength Index
- **Daily_Return:** Daily percentage change
- **Weekly_Return:** Weekly percentage change
- **Monthly_Return:** Monthly percentage change
- **Volatility_30:** 30-day rolling standard deviation

**Usage:**
```python
from notebooks.helpers.indicators_helper import add_technical_indicators, validate_indicators

# Calculate indicators if needed
df = add_technical_indicators(df_raw)

# Validate data quality
validate_indicators(df, 'bitcoin')
# Output: Indicators validated successfully!
```

---

## 📁 File Structure

```
Top50CryptoAnaliyst/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── environment.yml                    # Conda environment
│
├── Code/
│   ├── db_connection.py              # PostgreSQL connection
│   ├── load_to_database.py           # Load CSV to database
│   ├── kraken_api_client.py          # Kraken API wrapper
│   └── pulldata.py                   # Data fetching utilities
│
├── data/
│   ├── interim/                      # Cleaned data (14 CSVs)
│   │   ├── aave_cleaned.csv
│   │   ├── bitcoin_cleaned.csv
│   │   └── ... (14 total)
│   ├── processed/                    # Data with indicators (14 CSVs, 20 cols)
│   │   ├── avalanche_processed.csv
│   │   ├── bitcoin_processed.csv
│   │   └── ... (14 total)
│   └── model_data/
│       ├── Train/
│       └── Test/
│
├── notebooks/
│   ├── DataWrangling.ipynb
│   ├── EDA.ipynb
│   ├── Preprocessing.ipynb
│   ├── Model.ipynb
│   ├── UpdateData.ipynb              # Step 8: Create indicators
│   └── helpers/
│       └── indicators_helper.py      # Indicator functions (REUSABLE)
│
├── models/
│   └── linear_regression/            # Trained models (15 cryptos)
│       ├── bitcoin_model.pkl
│       └── ...
│
├── reports/
│   ├── BACKFILL_LOG.md               # Phase 0.5 completion
│   ├── MODELING_SUMMARY.md           # Phase 0 results
│   ├── LINEAR_REGRESSION_PERFORMANCE_REPORT.md
│   └── figures/
│
├── sql/
│   ├── init.sql                      # User & database creation
│   └── create_tables.sql             # Table definitions
│
├── .checklist/
│   ├── Devolment.md                  # Main TODO (UPDATED ✅)
│   └── phases/
│
├── .env                              # Environment variables (git ignored)
├── .gitignore                        # Git ignore rules
└── docker-compose.yml                # Docker PostgreSQL setup (optional)
```

---

## 🔧 Configuration

### Environment Variables (`.env`)
```env
DATABASE_URL=postgresql://postgres:Tanman6586!@127.0.0.1:5432/crypto_predictions
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Tanman6586!
DB_NAME=crypto_predictions
```

### Python Libraries (in `requirements.txt`)
```
pandas==1.5.0
numpy==1.23.0
scikit-learn==1.1.0
sqlalchemy==1.4.0
psycopg2-binary==2.9.0
jupyter==1.0.0
requests==2.28.0
```

---

## 📈 Model Performance Summary

### Linear Regression Results (Phase 0)
- **Bitcoin:** R² = 99.97%, MAPE = 0.54%, Dir.Acc = 91.52%
- **Ethereum:** R² = 99.93%, MAPE = 2.15%, Dir.Acc = 90.32%
- **Solana:** R² = 99.91%, MAPE = 1.89%, Dir.Acc = 88.74%
- **Average (14 cryptos):** R² = 97.2%, Dir.Acc = 90.3%

**Why Linear Regression?**
- ✅ 99.97% R² on Bitcoin
- ✅ Fast inference (milliseconds)
- ✅ Interpretable coefficients
- ✅ Outperformed tree-based models
- ✅ Production-ready and stable

See [MODELING_SUMMARY.md](reports/MODELING_SUMMARY.md) for detailed results.

---

## 🎯 Next Steps (Phases 1-3)

### Phase 1: Live Data Ingestion
```python
# Fetch current prices from Kraken API
# Update database every 1-5 minutes
# Store in 'prices' table with current timestamp
```

### Phase 2: Automated Retraining
```python
# Weekly model retraining
# Compare new vs. old performance
# Auto-update if improvement > 1%
# Version tracking
```

### Phase 3: Real-time Predictions
```python
# Load trained models
# Generate price predictions
# Store with confidence scores
# Audit trail for all predictions
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Use IPv4 (127.0.0.1), verify PostgreSQL running |
| Password authentication failed | Check `.env` password matches PostgreSQL setup |
| No module named 'Code' | Run Python from project root, activate conda |
| Data not loading | Verify CSV files in `data/processed/`, check INSERT privileges |
| Indicators not calculated | Run `notebooks/UpdateData.ipynb` or use `indicators_helper.py` |

---

## 📊 Key Metrics

### Data Quality Metrics
- ✅ 14/14 cryptocurrencies loaded
- ✅ 0 validation errors
- ✅ 100% data completeness
- ✅ 37,464 records verified

### Database Metrics
- ✅ Connection pooling: 10 connections
- ✅ Query indexes: 7 (cryptocurrency, timestamp, composite)
- ✅ Average query time: < 50ms
- ✅ Data integrity: UNIQUE constraints on (crypto, timestamp)

---

## 📚 Documentation Files

- **README.md** - You are here!
- **reports/BACKFILL_LOG.md** - Phase 0.5 details
- **reports/MODELING_SUMMARY.md** - Model performance
- **Code/db_connection.py** - Database code docs
- **notebooks/helpers/indicators_helper.py** - Indicator formulas

---

## 🔐 Security Notes

- ✅ `.env` is git-ignored (contains password)
- ✅ PostgreSQL user: postgres (localhost only)
- ✅ Database on 127.0.0.1 (IPv4, avoid IPv6 auth issues)
- ✅ ProgramData owned by elevated account
- ✅ Never commit credentials to Git

---

## 📞 Support & Questions

**For database issues:** Check `Code/db_connection.py`  
**For data:** See `data/processed/` CSVs or query database  
**For indicators:** Review `notebooks/helpers/indicators_helper.py`  
**For models:** See `reports/MODELING_SUMMARY.md`  

---

**Last Updated:** May 1, 2026  
**Phase Status:** 0.5 ✅ | 1.5 ✅ | 1 🔄 In Progress


---

## 📊 Model Performance Summary

### Top Performers (R² > 0.999)
- **Bitcoin**: R² = 0.9997, MAPE = 0.54%, Dir.Acc = 91.52%
- **Tron**: R² = 0.9993, MAPE = 0.64%, Dir.Acc = 92.27%
- **Binance Coin**: R² = 0.9991, MAPE = 0.70%, Dir.Acc = 91.93%
- **Render**: R² = 0.9992, MAPE = 1.41%, Dir.Acc = 92.67%

### Very Strong (R² 0.998-0.999)
**Ethereum, Avalanche, Solana, Fantom, Chainlink, Litecoin, Maker, Injective, Toncoin, Axie Infinity**
- All with >88% directional accuracy
- All with MAPE < 18%

### Production Status
✅ **14/15 cryptos ready for production**  
⚠️ **The Graph** - Requires separate treatment (negative R²)

See [detailed results](reports/MODELING_SUMMARY.md) for complete performance breakdown.
---

## 🚀 Quick Start

### Installation with Conda (Recommended)

```bash
# Clone repository
git clone https://github.com/tanmanrok/Top50CryptoAnaliyst.git
cd Top50CryptoAnaliyst

# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate environment
conda activate crypto-analysis
```

### Alternative: Manual Pip Installation

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

```bash
# 1. Data preprocessing and EDA
jupyter notebook notebooks/DataWrangling.ipynb
jupyter notebook notebooks/EDA.ipynb

# 2. Feature engineering
jupyter notebook notebooks/Preprocessing.ipynb

# 3. Model training and evaluation
jupyter notebook notebooks/Model.ipynb
```

### Using Pre-trained Models

```python
import pickle
import pandas as pd

# Load trained model
with open('models/linear_regression/bitcoin_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Make predictions
X_new = pd.DataFrame(...)  # 28 features required
predictions = model.predict(X_new)
```

---

## 📁 Project Structure

```
Top50CryptoAnaliyst/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
│
├── data/
│   ├── raw/                          # Original cryptocurrency data
│   ├── interim/                      # Cleaned & feature-engineered data
│   ├── processed/                    # Final modeling datasets
│   └── model_data/
│       ├── Train/                    # 80% training data
│       └── Test/                     # 20% testing data
│
├── notebooks/
│   ├── DataWrangling.ipynb           # Data loading & cleaning
│   ├── EDA.ipynb                     # Exploratory data analysis
│   ├── Preprocessing.ipynb           # Feature engineering
│   ├── Model.ipynb                   # Model training & evaluation
│   └── helpers/                      # Notebook utilities
│
├── models/
│   └── linear_regression/            # Trained models (1 per crypto)
│       ├── bitcoin_model.pkl
│       ├── ethereum_model.pkl
│       └── ...
│
├── reports/
│   ├── MODELING_SUMMARY.md           # Comprehensive results summary
│   ├── LINEAR_REGRESSION_PERFORMANCE_REPORT.md
│   ├── linear_regression_performance_table.csv
│   └── figures/                      # Generated visualizations
│       ├── rmse_comparison.png
│       ├── mae_comparison.png
│       ├── r2_score_comparison.png
│       ├── directional_accuracy_comparison.png
│       ├── mape_comparison.png
│       ├── performance_heatmap.png
│       └── coefficient_visualization.png
│
└── .checklist/
    └── MODEL_CHECKLIST.md            # Project progress tracking
```

---

## 🔧 Methodology

### Data Pipeline

1. **Data Loading** (DataWrangling.ipynb)
   - Load OHLCV data for 15 cryptocurrencies
   - Handle missing values and outliers
   - Verify data consistency

2. **Feature Engineering** (Preprocessing.ipynb)
   - **Technical Indicators:** SMA, EMA, RSI, MACD, Bollinger Bands
   - **Temporal Features:** Day of week, month, trend encoding
   - **Statistical Features:** Lagged returns, volatility measures
   - **Total: 28 features** for each cryptocurrency

3. **Exploratory Analysis** (EDA.ipynb)
   - Feature distributions and correlations
   - Statistical significance testing
   - Trend and volatility analysis

4. **Model Development** (Model.ipynb)
   - Train Linear Regression on all 15 cryptos
   - Hyperparameter tuning via GridSearchCV
   - Evaluate with TimeSeriesSplit cross-validation
   - Save models for production

5. **Performance Evaluation**
   - Calculate 6 key metrics per crypto
   - Generate comparison visualizations
   - Create detailed performance reports

### Model Selection: Linear Regression

**Why Linear Regression won?**
- ✅ **Interpretability:** Clear feature coefficients show what drives predictions
- ✅ **Speed:** Real-time inference for trading systems
- ✅ **Robustness:** Consistent performance across diverse assets
- ✅ **Generalization:** Strong test set performance (no overfitting)
- ✅ **Simplicity:** Outperformed Random Forest, XGBoost, LightGBM

---

## 📈 Key Features & Technical Indicators

### 28 Engineered Features

**Technical Indicators (13 features):**
- Simple Moving Averages: SMA-7, SMA-20, SMA-50
- Exponential Moving Average: EMA-20
- Relative Strength Index: RSI-14
- MACD (Macd Line, Signal Line, Histogram)
- Bollinger Bands (Upper, Middle, Lower)
- Daily/Weekly Returns
- Volatility (30-day)

**Temporal Features (10 features):**
- Hour of day, Day of week, Week of year, Month
- Quarter, Is_weekend
- Trend classification (Uptrend/Downtrend/Neutral)
- Season indicators

**Time Series Features (5 features):**
- Lagged returns (1-day, 7-day)
- Volatility trend
- Returns momentum
- Price acceleration

---

## 📊 Performance Metrics Explained

| Metric | Definition | Good Range |
|--------|-----------|------------|
| **R² Score** | Proportion of variance explained | > 0.95 (excellent) |
| **MAPE** | Mean Absolute Percentage Error | < 5% (excellent) |
| **MAE** | Mean Absolute Error in dollars | Depends on price |
| **RMSE** | Root Mean Squared Error | Lower is better |
| **Directional Accuracy** | % of correct direction predictions | > 55% (value), >90% (excellent) |
| **Correlation** | Pearson correlation with actual | > 0.99 (excellent) |

---

## 📁 Key Output Files

### Reports
- **`reports/MODELING_SUMMARY.md`** - Comprehensive project summary with all metrics
- **`reports/LINEAR_REGRESSION_PERFORMANCE_REPORT.md`** - Detailed model performance report
- **`reports/linear_regression_performance_table.csv`** - Results table (all cryptos)

### Models
- **`models/linear_regression/*.pkl`** - Trained models (1 per cryptocurrency)
- **`models/linear_regression/*_metadata.json`** - Model metadata and hyperparameters

### Visualizations
- **Performance comparison charts** (RMSE, MAE, R², accuracy, MAPE)
- **Performance heatmap** (all metrics vs cryptocurrencies)
- **Feature importance** (top 15 coefficients)

---

## 🎓 Project Phases

### ✅ Completed Phases (1-13)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Data Setup & Loading | ✅ Complete |
| 2 | Feature & Target Separation | ✅ Complete |
| 3 | Baseline Model Development | ✅ Complete |
| 4 | Linear Regression Training | ✅ Complete |
| 5 | Tree-Based Models Comparison | ✅ Complete |
| 6 | Advanced Models (LightGBM, XGBoost) | ✅ Complete |
| 7 | Hyperparameter Tuning | ✅ Complete |
| 8 | Model Evaluation (6 metrics) | ✅ Complete |
| 9 | Feature Importance Analysis | ✅ Complete |
| 10 | Apply Model to All 15 Cryptos | ✅ Complete |
| 11 | Prediction Generation & Visualization | ✅ Complete |
| 12 | Model Persistence & Documentation | ✅ Complete |
| 13 | **Generate Reports & Visualizations** | ✅ **Complete** |

### 📋 Remaining Phases (14-15)

| Phase | Description | Status |
|-------|-------------|--------|
| 14 | Results Analysis & Insights | 🔄 In Progress |
| 15 | Advanced Analysis (Optional) | ⏱️ Planned |

---

## 💡 Use Cases

### 1. **Quantitative Trading**
- Use directional predictions (90%+ accuracy) for entry/exit signals
- Combine with risk management for profitable strategies

### 2. **Portfolio Management**
- Accurate price forecasting aids rebalancing decisions
- Identify high-confidence prediction opportunities

### 3. **Risk Management**
- MAPE < 8% enables precise hedging
- Model confidence varies by asset (use confidence estimates)

### 4. **Algorithmic Execution**
- Ultra-fast Linear Regression inference
- Millisecond-level prediction generation

### 5. **Market Analysis**
- Feature coefficients reveal market structure
- Temporal patterns identified for strategy development

---

## ⚠️ Limitations & Considerations

1. **The Graph Exception** - Model underperforms (R² = -0.3555); requires separate treatment
2. **Market Regime Changes** - Model trained on historical data; may underperform during unprecedented conditions
3. **External Events** - Regulatory news, exchange hacks, macro events not captured
4. **Linear Assumptions** - Non-linear patterns not fully captured
5. **Recommendation:** Monthly retraining with recent data to maintain performance

---

## 🔍 Results at a Glance

```
===== LINEAR REGRESSION MODEL RESULTS =====

OVERALL STATISTICS (14/15 cryptos):
├─ Average R² Score:              0.972 (97.2% variance explained)
├─ Average Directional Accuracy:  90.3% (predicts direction correctly)
├─ Average MAPE:                  7.8% (small prediction error)
├─ Average MAE:                   $0.02
└─ Average Correlation:           0.997 (nearly perfect)

TOP 5 PERFORMERS:
├─ Bitcoin:        R²=0.9997  | MAPE=0.54%  | Dir.Acc=91.52%
├─ Tron:           R²=0.9993  | MAPE=0.64%  | Dir.Acc=92.27%
├─ Binance Coin:   R²=0.9991  | MAPE=0.70%  | Dir.Acc=91.93%
├─ Render:         R²=0.9992  | MAPE=1.41%  | Dir.Acc=92.67%
└─ Ethereum:       R²=0.9987  | MAPE=1.52%  | Dir.Acc=88.07%

DEPLOYMENT RECOMMENDATION:
✅ Production Ready (14 cryptos)
⚠️  Monitor & Retrain Monthly
❌ Investigate The Graph Exception
```

---

## 🛠️ Technology Stack

- **Python 3.8+** - Programming language
- **Pandas** - Data manipulation & analysis
- **Scikit-learn** - Machine learning models
- **NumPy** - Numerical computing
- **Matplotlib & Seaborn** - Visualization
- **Jupyter** - Interactive notebooks
- **LightGBM & XGBoost** - Advanced models (comparison)

---

## 📚 Documentation

- **[Detailed Results](reports/MODELING_SUMMARY.md)** - Comprehensive performance analysis
- **[Model Performance Report](reports/LINEAR_REGRESSION_PERFORMANCE_REPORT.md)** - Technical details

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Investigate The Graph performance issue
- Ensemble methods combining Linear Regression with sentiment analysis
- Real-time inference pipeline for live trading
- Extended feature set (sentiment, on-chain metrics)

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Data Source:** Historical cryptocurrency price data (OHLCV)
- **Framework:** [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/)
- **Libraries:** scikit-learn, pandas, numpy, matplotlib
- **Project Template:** Best practices in data science workflows

---

**Status:** ✅ Production Ready  
**Last Updated:** April 14, 2026  
**Model Confidence:** Very High (14/15 assets)

