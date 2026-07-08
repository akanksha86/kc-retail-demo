#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
REGION="EU"
DATASET_ID="raw_retail_data"
GCS_URI="gs://kc-retail-demo-warehouse/unstructured/*"
CONNECTION_NAME="retail_object_conn"
VERTEX_CONN_NAME="retail_vertex_conn"

echo "================================================="
echo "Setting up Unstructured Data Insights & BigQuery"
echo "================================================="

echo "1. Enabling required APIs..."
gcloud services enable \
    biglake.googleapis.com \
    aiplatform.googleapis.com \
    dataplex.googleapis.com \
    --project="$PROJECT_ID"

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


echo "3. Creating Vertex AI Connection for Gemini..."
if ! bq show --connection --project_id="$PROJECT_ID" --location="$REGION" "$VERTEX_CONN_NAME" >/dev/null 2>&1; then
    bq mk --connection \
        --connection_type=CLOUD_RESOURCE \
        --project_id="$PROJECT_ID" \
        --location="$REGION" \
        "$VERTEX_CONN_NAME"
fi

VERTEX_SA=$(bq show --format=json --connection --project_id="$PROJECT_ID" --location="$REGION" "$VERTEX_CONN_NAME" | jq -r '.cloudResource.serviceAccountId')
echo "Granting Vertex AI User permissions to Connection SA: $VERTEX_SA"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${VERTEX_SA}" \
    --role="roles/aiplatform.user"

echo "Waiting 60 seconds for IAM propagation..."
sleep 60

echo "4. Creating BigQuery Object Table for PDFs..."
bq query --use_legacy_sql=false \
"CREATE OR REPLACE EXTERNAL TABLE \`${PROJECT_ID}.${DATASET_ID}.unstructured_docs\`
WITH CONNECTION \`${PROJECT_ID}.${REGION}.${CONNECTION_NAME}\`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['${GCS_URI}']
);"

echo "5. Creating Remote Gemini Model in BigQuery..."
bq query --use_legacy_sql=false \
"CREATE OR REPLACE MODEL \`${PROJECT_ID}.${DATASET_ID}.gemini_2_5_pro\`
REMOTE WITH CONNECTION \`${PROJECT_ID}.${REGION}.${VERTEX_CONN_NAME}\`
OPTIONS (endpoint = 'gemini-2.5-pro');"

echo "================================================="
echo "Setup Complete!"
echo ""
echo "Try running this SQL query in BigQuery to extract metadata from PDFs and join it with structured data:"
echo ""
echo "SELECT "
echo "  structured.product_name,"
echo "  structured.unit_price,"
echo "  extracted_data.ml_generate_content_result as llm_extraction"
echo "FROM ML.GENERATE_CONTENT("
echo "  MODEL \`${PROJECT_ID}.${DATASET_ID}.gemini_2_5_pro\`,"
echo "  ("
echo "    SELECT uri AS prompt, data FROM \`${PROJECT_ID}.${DATASET_ID}.unstructured_docs\`"
echo "    WHERE uri LIKE '%manual%'"
echo "  ),"
echo "  STRUCT("
echo "    'Extract the exact SKU and summarize the maintenance instructions in 1 sentence. Output in JSON format with keys: \"sku\" and \"maintenance\".' AS system_instruction,"
echo "    TRUE AS flatten_json_output"
echo "  )"
echo ") AS extracted_data"
echo "INNER JOIN \`${PROJECT_ID}.${DATASET_ID}.products\` AS structured"
echo "  ON JSON_VALUE(extracted_data.ml_generate_content_result, '$.sku') = structured.sku"
echo "LIMIT 10;"
echo "================================================="
