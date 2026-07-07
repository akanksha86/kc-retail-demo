#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change directory to the workspace root directory containing this script
cd "$(dirname "$0")/.."

echo "============================================="
echo "Acme Retail - BigQuery Synthetic Data Uploader"
echo "============================================="

# 1. Check if virtual environment exists, if not, create it
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

# 2. Activate virtual environment and install bigquery client
echo "Checking and installing required python dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install google-cloud-bigquery

# 3. Check for active gcloud account
echo "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "WARNING: No active gcloud account detected. Running gcloud login flow..."
    gcloud auth login
    gcloud auth application-default login
fi

# 4. Prompt for project and dataset details
read -p "Enter Google Cloud Project ID [default: kc-retail-demo]: " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-kc-retail-demo}
read -p "Enter BigQuery Dataset ID [default: raw_retail_data]: " DATASET_ID
DATASET_ID=${DATASET_ID:-raw_retail_data}
read -p "Enter Dataset Location (e.g. US, EU) [default: US]: " LOCATION
LOCATION=${LOCATION:-US}

# 5. Execute python upload script
echo "Starting data upload to BigQuery..."
CMD=".venv/bin/python scripts/upload_to_bq.py --dataset_id $DATASET_ID --location $LOCATION"
if [ -n "$PROJECT_ID" ]; then
    CMD="$CMD --project_id $PROJECT_ID"
fi

eval $CMD

echo "============================================="
echo "Ingestion Finished Successfully!"
echo "============================================="
