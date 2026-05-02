#!/bin/bash
# Initialize PostgreSQL with user, database, and tables

set -e

# Source postgres functions
source /usr/local/bin/docker-entrypoint.sh

# This will run the standard docker-entrypoint logic which creates postgres user
_main "$@" &
MAINPID=$!
wait "$MAINPID"

# Now create crypto_user and database
psql -U postgres -tc "SELECT 1 FROM pg_user WHERE usname = 'crypto_user'" | grep -q 1 || psql -U postgres -c "CREATE USER crypto_user WITH PASSWORD 'crypto_password';"
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'crypto_predictions'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE crypto_predictions OWNER crypto_user;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crypto_predictions TO crypto_user;"

# Create tables in crypto_predictions database
psql -U postgres -d crypto_predictions <<EOF
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    cryptocurrency VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cryptocurrency, timestamp)
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    cryptocurrency VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT,
    price_at_prediction FLOAT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    cryptocurrency VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp);
CREATE INDEX IF NOT EXISTS idx_prices_cryptocurrency ON prices(cryptocurrency);
CREATE INDEX IF NOT EXISTS idx_prices_crypto_time ON prices(cryptocurrency, timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_cryptocurrency ON predictions(cryptocurrency);
CREATE INDEX IF NOT EXISTS idx_metrics_cryptocurrency ON metrics(cryptocurrency);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
EOF

exec "$@"
