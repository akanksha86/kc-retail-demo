#!/usr/bin/env bash

set -e
cd "$(dirname "$0")/.."

PROJECT_ID="kc-retail-demo"
DATASET_ID="raw_retail_data_euw1"

echo "================================================="
echo "Training BigQuery ML Model & Registering to Vertex AI"
echo "================================================="
echo "This script trains a K-Means clustering model on our retail data"
echo "and automatically registers it to the Vertex AI Model Registry."
echo "Knowledge Catalog will automatically crawl and catalog this model!"
echo "================================================="

bq query --use_legacy_sql=false \
"CREATE OR REPLACE MODEL \`${PROJECT_ID}.${DATASET_ID}.customer_segmentation_model\`
OPTIONS(
  model_type='kmeans',
  num_clusters=4,
  model_registry='vertex_ai',
  vertex_ai_model_id='retail_customer_segmentation'
) AS
SELECT 
  c.customer_segment,
  COUNT(o.order_id) as total_orders,
  SUM(o.total_amount) as total_spend,
  AVG(oi.quantity) as avg_item_quantity
FROM \`${PROJECT_ID}.${DATASET_ID}.customers\` c
JOIN \`${PROJECT_ID}.${DATASET_ID}.orders\` o ON c.customer_id = o.customer_id
JOIN \`${PROJECT_ID}.${DATASET_ID}.order_items\` oi ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.customer_segment;"

echo "================================================="
echo "Model Training Complete!"
echo "You can view this model in the Vertex AI Model Registry in the Google Cloud Console."
echo "================================================="
