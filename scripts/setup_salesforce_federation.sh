#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
REGION="europe-west1"
DATASET_ID="raw_retail_data_euw1"
BUCKET_NAME="${PROJECT_ID}-warehouse"

echo "================================================="
echo "Simulating Zero-Copy Salesforce Federation"
echo "================================================="
echo "Note: In a production environment, this would be achieved natively via"
echo "Salesforce Data Cloud direct integration or BigQuery Omni."
echo "Here, we simulate the federated CRM data using an external table over GCS."
echo "================================================="

# Check if data exists
if [ ! -f "data/salesforce_service_cases.csv" ]; then
    echo "Salesforce data not found. Generating..."
    python3 scripts/generate_salesforce_data.py
fi

echo "1. Uploading synthetic Salesforce service cases to GCS..."
gcloud storage cp data/salesforce_service_cases.csv "gs://${BUCKET_NAME}/salesforce/service_cases.csv"

echo "2. Creating BigQuery External Table for Salesforce Data..."
# Create external table definition using bq mk
bq query --use_legacy_sql=false \
"CREATE OR REPLACE EXTERNAL TABLE \`${PROJECT_ID}.${DATASET_ID}.salesforce_service_cases\`
OPTIONS (
  format = 'CSV',
  uris = ['gs://${BUCKET_NAME}/salesforce/service_cases.csv'],
  skip_leading_rows = 1
);"

echo "================================================="
echo "Setup Complete!"
echo "You can query the federated Salesforce data in BigQuery:"
echo "SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.salesforce_service_cases\` LIMIT 10;"
