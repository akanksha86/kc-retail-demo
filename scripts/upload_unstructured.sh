#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change directory to the workspace root directory containing this script
cd "$(dirname "$0")/.."

echo "============================================="
echo "Acme Retail - GCS Unstructured Data Uploader"
echo "============================================="

read -p "Enter Google Cloud Project ID [default: kc-retail-demo]: " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-kc-retail-demo}
read -p "Enter Target GCS Bucket (without gs://) [default: kc-retail-demo-warehouse]: " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-kc-retail-demo-warehouse}

# 1. Check for active gcloud account
echo "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "WARNING: No active gcloud account detected. Running gcloud login flow..."
    gcloud auth login
    gcloud auth application-default login
fi

echo "Uploading unstructured data to gs://${BUCKET_NAME}/unstructured/ ..."

# Upload Manuals
gcloud storage cp -r data/unstructured/manuals gs://${BUCKET_NAME}/unstructured/

# Upload SOPs
gcloud storage cp -r data/unstructured/sops gs://${BUCKET_NAME}/unstructured/

# Upload Contracts
gcloud storage cp -r data/unstructured/contracts gs://${BUCKET_NAME}/unstructured/

echo "============================================="
echo "GCS Upload Finished Successfully!"
echo "Your unstructured PDFs are ready for Knowledge Catalog GCS Discovery."
echo "============================================="
