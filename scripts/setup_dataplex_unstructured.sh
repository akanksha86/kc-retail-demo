#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
REGION="europe-west1"
DATASET_ID="raw_retail_data_euw1"
GCS_URI="gs://kc-retail-demo-warehouse/unstructured/*"
CONNECTION_NAME="retail_object_conn_euw1"

echo "================================================="
echo "Setting up Europe-West1 Dataset for Dataplex Insights"
echo "================================================="

echo "1. Creating dataset in $REGION..."
bq mk --dataset --location="$REGION" "${PROJECT_ID}:${DATASET_ID}" || true

echo "2. Creating BigLake Connection for Object Tables..."
if ! bq show --connection --project_id="$PROJECT_ID" --location="$REGION" "$CONNECTION_NAME" >/dev/null 2>&1; then
    bq mk --connection \
        --connection_type=CLOUD_RESOURCE \
        --project_id="$PROJECT_ID" \
        --location="$REGION" \
        "$CONNECTION_NAME"
fi

SA_EMAIL=$(bq show --format=json --connection --project_id="$PROJECT_ID" --location="$REGION" "$CONNECTION_NAME" | jq -r '.cloudResource.serviceAccountId')
echo "Granting GCS read permissions to Connection SA: $SA_EMAIL"
gcloud storage buckets add-iam-policy-binding gs://kc-retail-demo-warehouse \
    --project="$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectViewer"

echo "Waiting 60 seconds for IAM propagation..."
sleep 60

echo "3. Creating BigQuery Object Table for PDFs in $REGION..."
bq query --use_legacy_sql=false \
"CREATE OR REPLACE EXTERNAL TABLE \`${PROJECT_ID}.${DATASET_ID}.unstructured_docs\`
WITH CONNECTION \`${PROJECT_ID}.${REGION}.${CONNECTION_NAME}\`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['${GCS_URI}']
);"

echo "Setup Complete! You can now run trigger_unstructured_dataplex_scan.py"
