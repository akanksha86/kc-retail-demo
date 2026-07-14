#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
REGION="europe-west1"
DATASET_ID="raw_retail_data_euw1"
BUCKET_NAME="${PROJECT_ID}-warehouse"

echo "================================================="
echo "Simulating Managed Connectivity for Legacy Databases"
echo "================================================="
echo "Note: In a production environment, this data would be accessed via"
echo "Cloud SQL federated queries (zero-copy) or replicated continuously"
echo "via Datastream into BigQuery."
echo "Here, we simulate an on-premise PostgreSQL 'suppliers' database"
echo "using an external table over GCS."
echo "================================================="

if [ ! -f "data/suppliers.csv" ]; then
    echo "Suppliers data not found. Generating..."
    python3 scripts/generate_suppliers.py
fi

echo "1. Uploading synthetic Postgres suppliers data to GCS..."
gcloud storage cp data/suppliers.csv "gs://${BUCKET_NAME}/postgres/suppliers.csv"

echo "2. Creating BigQuery External Table for Postgres Data..."
bq query --use_legacy_sql=false \
"CREATE OR REPLACE EXTERNAL TABLE \`${PROJECT_ID}.${DATASET_ID}.postgres_suppliers\`
OPTIONS (
  format = 'CSV',
  uris = ['gs://${BUCKET_NAME}/postgres/suppliers.csv'],
  skip_leading_rows = 1
);"

echo "================================================="
echo "Setup Complete!"
echo "You can query the federated PostgreSQL data in BigQuery:"
echo "SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.postgres_suppliers\` LIMIT 10;"
