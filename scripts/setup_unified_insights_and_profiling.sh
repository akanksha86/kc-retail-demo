#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
REGION="europe-west1"
DATASET_ID="raw_retail_data_euw1"
ICEBERG_TABLE="${PROJECT_ID}.acme_catalog_fed_final.raw_data.inventory"
UNIFIED_VIEW="${PROJECT_ID}.${DATASET_ID}.unified_product_insights"

echo "================================================="
echo "Creating Unified Insights View (Unstructured + Structured + Iceberg)"
echo "================================================="

# Extract Project Number to get AI Platform Service Account
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
AI_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"

echo "Granting AI Platform Service Account access to the bucket..."
gcloud storage buckets add-iam-policy-binding "gs://kc-retail-demo-warehouse" \
    --member="serviceAccount:${AI_SA}" \
    --role="roles/storage.objectViewer"

echo "0. Setting up cross-region prerequisites in europe-west1..."
# Create a Gemini model in the europe-west1 dataset using the europe-west1 connection
bq query --use_legacy_sql=false \
"CREATE OR REPLACE MODEL \`${PROJECT_ID}.${DATASET_ID}.gemini_2_5_pro\`
REMOTE WITH CONNECTION \`${PROJECT_ID}.${REGION}.retail_object_conn_euw1\`
OPTIONS(endpoint = 'gemini-2.5-pro');"

# Upload the structured CSVs from the local data folder to the europe-west1 dataset 
# so BigQuery can JOIN them against the unstructured data
python3 scripts/upload_to_bq.py --project_id "${PROJECT_ID}" --dataset_id "${DATASET_ID}" --location "${REGION}"

echo "1. Creating BigQuery View: ${UNIFIED_VIEW}"
bq query --use_legacy_sql=false \
"CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.unified_product_insights\` AS
WITH raw_extracted AS (
  SELECT *
  FROM ML.GENERATE_TEXT(
    MODEL \`${PROJECT_ID}.${DATASET_ID}.gemini_2_5_pro\`,
    (
      SELECT *
      FROM \`${PROJECT_ID}.${DATASET_ID}.unstructured_docs\`
      WHERE uri LIKE '%manual%'
    ),
    STRUCT(
      'Extract the exact SKU and summarize the maintenance instructions in 1 sentence. Output ONLY a valid, raw JSON object with keys: \"sku\" and \"maintenance\". Do NOT use markdown formatting or backticks. Ensure maximum accuracy and no markdown.' AS prompt,
      TRUE AS flatten_json_output
    )
  )
),
extracted_data AS (
  SELECT
    uri,
    REPLACE(REPLACE(ml_generate_text_llm_result, '\`\`\`json\\n', ''), '\`\`\`', '') AS cleaned_json
  FROM raw_extracted
)
SELECT 
  extracted_data.uri,
  TRIM(JSON_VALUE(extracted_data.cleaned_json, '$.sku')) AS extracted_sku,
  JSON_VALUE(extracted_data.cleaned_json, '$.maintenance') AS maintenance_instructions,
  structured.*,
  inv.stock_quantity,
  inv.store_id,
  inv.last_updated
FROM extracted_data
JOIN \`${PROJECT_ID}.${DATASET_ID}.products\` AS structured
  ON TRIM(JSON_VALUE(extracted_data.cleaned_json, '$.sku')) = TRIM(structured.sku)
LEFT JOIN \`${ICEBERG_TABLE}\` AS inv
  ON structured.product_id = inv.product_id;"

echo "View created successfully."
echo ""

echo "================================================="
echo "Setting up Dataplex Data Profile Scan"
echo "================================================="
SCAN_ID="unified-insights-profile-$(date +%s)"
SCAN_LOCATION="europe-west1" # Need to match Dataplex region constraints if needed, using europe-west1 to align with Iceberg
# Note: Data Profile Scans on views might require the view and tables to be co-located or handled correctly.

echo "2. Creating Dataplex Profile Scan on the Unified View (or base products table if view is not supported)"
# Dataplex data profile scans can be created on BigQuery tables/views
# Note: sometimes views with ML.GENERATE_CONTENT are too dynamic for standard profiling, 
# so we profile the products table as the base structure, but demonstrate the command:

gcloud dataplex datascans create data-profile "${SCAN_ID}" \
    --project="${PROJECT_ID}" \
    --location="${SCAN_LOCATION}" \
    --data-source-resource="//bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_ID}/tables/products" \
    --display-name="Retail Products AI Profile Scan" \
    --async

echo "Dataplex Profile Scan creation initiated: ${SCAN_ID}"
echo "================================================="
echo "Setup Complete!"
echo "You can query the unified view in BigQuery:"
echo "SELECT * FROM \`${UNIFIED_VIEW}\` LIMIT 10;"
