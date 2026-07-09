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
bq query --use_legacy_sql=false \
"CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.extracted_manual_insights\` AS
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
)
SELECT
  uri,
  JSON_VALUE(REPLACE(REPLACE(ml_generate_text_llm_result, '\`\`\`json\\n', ''), '\`\`\`', ''), '$.sku') as sku,
  JSON_VALUE(REPLACE(REPLACE(ml_generate_text_llm_result, '\`\`\`json\\n', ''), '\`\`\`', ''), '$.maintenance') as maintenance_summary,
  CURRENT_TIMESTAMP() as extracted_at
FROM raw_extracted;"

echo "================================================="
