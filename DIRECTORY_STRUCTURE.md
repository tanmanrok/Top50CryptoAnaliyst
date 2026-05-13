# Project Structure Guide

## Root Directory (Entry Points)
```
README.md                  # Main project documentation
run_tests.py              # Test runner - run before pushing
requirements.txt          # Python dependencies
environment.yml           # Conda environment file
docker-compose.yml        # Docker services configuration
pytest.ini                # Pytest configuration
.env                      # Environment variables (DO NOT COMMIT)
.env.example              # Environment variables template
.gitignore                # Git ignore rules
```

## Core Directories

### `Code/` - Application Source Code
```
Code/
├── __init__.py
├── live_data_fetcher.py        # Main data fetching service
├── load_to_database.py
├── data/                       # Data fetching & preparation
│   ├── db_connection.py        # PostgreSQL connection
│   ├── kraken_api_client.py   # Kraken API wrapper
│   ├── kraken_live_fetcher.py # Live data fetching
│   ├── pipeline.py
│   └── ...
├── features/                   # Feature engineering
│   ├── compute_features.py
│   ├── backfill_features.py
│   ├── live_features_service.py
│   └── test_features.py
├── models/                     # Model training & prediction
│   ├── train_model_v2.py
│   ├── predict_v2.py
│   ├── prepare_data_v2.py
│   ├── retrain_model_v2.py
│   └── validate_timeseries_v2.py
└── utils/                      # Utility functions
    └── __init__.py
```

### `scripts/` - Utility & Helper Scripts
```
scripts/
├── check_latest.py              # Check latest data status
├── cleanup_dups.py              # Remove duplicate records
├── cleanup_json.py              # Clean JSON files
├── fix_json_structure.py        # Fix malformed JSON
├── update_features_simple.py    # Simple feature update
├── run_7day_validation.py       # 7-day model validation runner
└── run_prediction_manual.py     # Manual prediction runner
```

### `docs/` - Documentation & Security Guides
```
docs/
├── SECURITY_AUDIT_REPORT.md     # Security audit findings
├── VALIDATION_7DAY_SETUP.md     # Validation setup guide
├── pre_push_security_check.ps1  # PowerShell security checks
└── pre_push_security_check.sh   # Bash security checks
```

### `tests/` - Test Suite
```
tests/
├── conftest.py                  # Pytest fixtures & configuration
├── test_data_preparation.py     # Data preparation tests
├── test_model_training.py       # Model training tests
├── test_error_handling.py       # Error handling tests
├── test_integration.py          # Integration tests
├── test_performance.py          # Performance benchmarks
├── test_prediction_service.py   # Prediction service tests
└── fixtures/                    # Test data
```

### `data/` - Data Files
```
data/
├── raw/                         # Raw data from API
├── interim/                     # Intermediate processed data
├── processed/                   # Final processed data
├── model_data/                  # Data for model training
└── validation/                  # Validation datasets
```

### `models/` - Model Artifacts
```
models/
├── v2_final_Ridge_bitcoin.pkl                  # Trained model
├── v2_final_scaler_X_bitcoin.pkl              # Feature scaler
├── v2_final_scaler_y_bitcoin.pkl              # Target scaler
├── v2_final_Ridge_bitcoin_metadata.json       # Model metadata
└── v2_final_Ridge_bitcoin_report.txt          # Model report
```

### `notebooks/` - Jupyter Notebooks
```
notebooks/
├── DataWrangling.ipynb          # Data preparation examples
├── EDA.ipynb                    # Exploratory data analysis
├── Model.ipynb                  # Model development
├── Model_v2.ipynb               # Model v2 development
├── Preprocessing.ipynb          # Data preprocessing
├── UpdateData.ipynb             # Data update workflows
└── helpers/                     # Helper utilities for notebooks
```

### `sql/` - Database Setup
```
sql/
├── create_tables.sql            # Database schema
├── init.sql                     # Data initialization
└── docker-entrypoint.sh         # Docker startup script
```

### `reports/` - Analysis Reports
```
reports/
├── MODELING_SUMMARY.md          # Model development summary
├── VALIDATION_7DAY.md           # 7-day validation results
├── LINEAR_REGRESSION_PERFORMANCE_REPORT.md
└── figures/                     # Report visualizations
```

### Other Directories
```
logs/                    # Application logs
references/             # Reference materials & documentation
.vscode/                # VS Code workspace settings
.git/                   # Git version control
```

---

## Quick Start

### Before Pushing to GitHub:
```bash
# 1. Run security checks
.\docs\pre_push_security_check.ps1

# 2. Run all tests
python run_tests.py

# 3. Check git status
git status

# 4. Add files and commit
git add .
git commit -m "Your commit message"

# 5. Push
git push
```

### Running Tests:
```bash
# All tests
python run_tests.py

# Unit tests only (fast)
python run_tests.py unit

# Integration tests
python run_tests.py integration

# With coverage
python run_tests.py coverage
```

### Utilities in scripts/:
```bash
# Check latest data
python scripts/check_latest.py

# Clean up duplicates
python scripts/cleanup_dups.py

# Update features
python scripts/update_features_simple.py

# Run 7-day validation
python scripts/run_7day_validation.py

# Manual prediction
python scripts/run_prediction_manual.py
```

---

## Important Files

| File | Purpose | When Used |
|------|---------|-----------|
| `run_tests.py` | Main test runner | Before every push |
| `requirements.txt` | Python dependencies | `pip install -r requirements.txt` |
| `environment.yml` | Conda environment | `conda env create -f environment.yml` |
| `.env` | **DO NOT COMMIT** | Local credentials (git ignored) |
| `pytest.ini` | Test configuration | Automatic (used by pytest) |

---

## Directory Statistics

```
Code/              → Application logic & models
scripts/           → 7 utility scripts (was in root)
docs/              → 4 documentation files (was in root)
tests/             → 177+ tests across 6 files
notebooks/         → 6 Jupyter notebooks
data/              → Raw, interim, and processed datasets
models/            → Trained model artifacts (6 files)
reports/           → Analysis and validation reports
```

**Total root files reduced from 40+ to 8 clean entry points** ✅

