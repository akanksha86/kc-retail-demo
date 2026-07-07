#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change directory to the workspace root directory containing this script
cd "$(dirname "$0")/.."

echo "================================================="
echo "Acme Retail - BigLake Unity Catalog Federation"
echo "================================================="

# Set variables
PROJECT_ID="kc-retail-demo"
REGION="europe-west1"
SECRET_NAME="databricks-oauth-creds"
CATALOG_NAME="acme_catalog_fed_final"
UNITY_INSTANCE_NAME="1030582515160828.8.gcp.databricks.com"
UNITY_CATALOG_NAME="acme_catalog"

# 1. Enable required APIs
echo "Enabling BigLake and Secret Manager APIs..."
gcloud services enable biglake.googleapis.com secretmanager.googleapis.com --project="$PROJECT_ID"

# 2. Get Databricks OAuth Credentials
echo "Please provide your Databricks Service Principal Credentials."
echo "These credentials will be stored securely in GCP Secret Manager."
read -p "Enter Databricks Client ID: " CLIENT_ID
read -sp "Enter Databricks Client Secret: " CLIENT_SECRET
echo ""

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "Error: Both Client ID and Client Secret must be provided."
    exit 1
fi

# 3. Create temporary credentials JSON file
CREDENTIALS_FILE="credentials_temp.json"
cat <<EOF > "$CREDENTIALS_FILE"
{
  "client_id": "$CLIENT_ID",
  "client_secret": "$CLIENT_SECRET"
}
EOF

# Ensure cleanup of temp credentials file even if script fails/exits
cleanup() {
  if [ -f "$CREDENTIALS_FILE" ]; then
    echo "Cleaning up temporary credentials file..."
    rm -f "$CREDENTIALS_FILE"
  fi
}
trap cleanup EXIT

# 4. Set Secret Manager API override for europe-west1
echo "Configuring Secret Manager regional endpoint for $REGION..."
gcloud config set api_endpoint_overrides/secretmanager "https://secretmanager.${REGION}.rep.mtls.googleapis.com/"

# 5. Create regional secret in Secret Manager
echo "Creating Secret Manager secret '$SECRET_NAME' in location '$REGION'..."
# Check if secret already exists, if so overwrite/add version or recreate.
if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" --location="$REGION" >/dev/null 2>&1; then
    echo "Secret '$SECRET_NAME' already exists. Adding new version..."
    gcloud secrets versions add "$SECRET_NAME" --project="$PROJECT_ID" --location="$REGION" --data-file="$CREDENTIALS_FILE"
else
    gcloud secrets create "$SECRET_NAME" \
      --location="$REGION" \
      --project="$PROJECT_ID" \
      --data-file="$CREDENTIALS_FILE"
fi

# 6. Create the BigLake Iceberg Federated Catalog
echo "Creating BigLake Iceberg federated catalog '$CATALOG_NAME' pointing to Databricks Unity Catalog..."

# Check if catalog already exists
if gcloud alpha biglake iceberg catalogs describe "$CATALOG_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Federated catalog '$CATALOG_NAME' already exists. Skipping creation."
else
    gcloud alpha biglake iceberg catalogs create "$CATALOG_NAME" \
       --project="$PROJECT_ID" \
       --primary-location="$REGION" \
       --catalog-type="federated" \
       --federated-catalog-type="unity" \
       --secret-name="projects/$PROJECT_ID/locations/$REGION/secrets/$SECRET_NAME" \
       --unity-instance-name="$UNITY_INSTANCE_NAME" \
       --unity-catalog-name="$UNITY_CATALOG_NAME" \
       --refresh-interval="300s"
    echo "Created BigLake Iceberg catalog '$CATALOG_NAME'."
fi

# 7. Grant the catalog service account access to the Secret
echo "Retrieving BigLake Catalog service account ID..."
BIGLAKE_SA=$(gcloud alpha biglake iceberg catalogs describe "$CATALOG_NAME" \
    --project="$PROJECT_ID" \
    --format="json" | grep -o '"[^"]*@gcp-sa-biglakerestcatalog.iam.gserviceaccount.com"' | tr -d '"' | head -n 1)

echo "BigLake Service Account Email: $BIGLAKE_SA"

echo "Waiting 15 seconds for the new Service Account to propagate to IAM..."
sleep 15

echo "Granting Secret Accessor role to the BigLake Service Account..."
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --member="serviceAccount:$BIGLAKE_SA" \
    --role="roles/secretmanager.secretAccessor"

echo "Granting Storage Object Viewer role to BigLake Service Account for Iceberg data access..."
gcloud storage buckets add-iam-policy-binding gs://kc-retail-demo-warehouse \
    --project="$PROJECT_ID" \
    --member="serviceAccount:$BIGLAKE_SA" \
    --role="roles/storage.objectViewer"

# Reset config override for safety
gcloud config unset api_endpoint_overrides/secretmanager

echo "================================================="
echo "BigQuery Lakehouse Federation Setup Complete!"
echo "You can now query federated tables in BigQuery using:"
echo "SELECT * FROM \`$PROJECT_ID\`.${CATALOG_NAME}.raw_data.inventory LIMIT 10;"
echo "================================================="
