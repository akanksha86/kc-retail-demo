# Walkthrough: Acme Retail Synthetic Data & Databricks Iceberg Federation

We have completed the setup of the synthetic retail dataset generation for **Acme Retail** and configured the deployment files and scripts to federate Databricks Unity Catalog metadata to BigQuery.

This walkthrough outlines:
1. **Phase 1**: Local dataset stats and local BigQuery loading.
2. **Phase 2**: Step-by-step setup for Apache Iceberg on GCS, Databricks Unity Catalog integration, and BigLake federation.

---

## Prerequisites & Setup

Before starting the phases below, ensure your environment is configured.

### 1. Python Environment Setup
Create and activate a virtual environment, then install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Cloud Authentication
Authenticate with your GCP environment using Application Default Credentials (ADC):
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>
```

---

## Phase 1: Local Dataset & BigQuery Raw Table Loading

The synthetic generator produced 6 highly integrated tables in `data/`:
* `stores.csv` (23 rows): master store locations (22 physical, 1 online).
* `products.csv` (1,500 rows): retail items with unit prices and unique SKUs.
* `customers.csv` (20,000 rows): global customer demographic profiles.
* `orders.csv` (100,000 rows): customer orders.
* `order_items.csv` (349,016 rows): transactional items mapping orders to products.
* `inventory.csv` (32,752 rows): store inventory snapshots.

### Local Ingestion into BigQuery
To load these files into your Google Cloud project:
1. Open your terminal.
2. Run the wrapper script from the project root:
   ```bash
   ./scripts/upload.sh
   ```
3. Follow the prompts to configure your target GCP project and BigQuery dataset.

---

## Phase 2: Databricks Unity Catalog & Apache Iceberg Federation

We will create an Apache Iceberg table for the `inventory` dataset on Google Cloud Storage (GCS), register it in Databricks Unity Catalog, and federate its metadata to BigQuery.

### Prerequisites & Step-by-Step Setup

#### Step 1: Create the GCS Bucket
Create a regional GCS bucket to hold your Iceberg data:
```bash
gcloud storage buckets create gs://<YOUR_GCS_BUCKET> \
  --location=<YOUR_REGION> \
  --project=<YOUR_PROJECT_ID>
```

#### Step 2: Upload the Raw Inventory Data
Copy the synthetic inventory data to GCS so Databricks can access and process it:
```bash
gcloud storage cp data/inventory.csv gs://<YOUR_GCS_BUCKET>/raw/inventory.csv
```

#### Step 3: Grant Databricks Access to GCS (Storage Credentials)
Configure Databricks Unity Catalog to read and write to the GCS bucket:
1. Log into your Databricks Workspace.
2. Navigate to **Catalog** -> **External Data** -> **Storage Credentials**.
3. Create a Storage Credential. Databricks will generate a GCP Service Account email for this credential.
4. Copy the GCP Service Account email and grant it permissions on your GCS bucket:
   ```bash
   gcloud storage buckets add-iam-policy-binding gs://<YOUR_GCS_BUCKET> \
     --member="serviceAccount:<DATABRICKS_GENERATED_SERVICE_ACCOUNT>" \
     --role="roles/storage.objectAdmin"

   gcloud storage buckets add-iam-policy-binding gs://<YOUR_GCS_BUCKET> \
     --member="serviceAccount:<DATABRICKS_GENERATED_SERVICE_ACCOUNT>" \
     --role="roles/storage.legacyBucketReader"
   ```
5. In Databricks, navigate to **Catalog** -> **External Data** -> **External Locations**.
6. Click **Create Location**, set the URL to `gs://<YOUR_GCS_BUCKET>/`, name it, and select the Storage Credential you created.

#### Step 4: Create a Databricks Service Principal
To allow BigQuery to read metadata from Databricks Unity Catalog, create an OAuth Service Principal:
1. Go to your Databricks Account Console.
2. Navigate to **User Management** -> **Service Principals** and click **Add service principal**.
3. Enter a name (e.g. `bigquery-federation-sp`) and click **Add**.
4. Copy the **Application ID** (this will be your `client_id`).
5. Open the service principal page, go to the **Secrets** tab, click **Generate secret**, and copy the secret value (this will be your `client_secret`).
6. **Assign Permissions**: In the Databricks Catalog Explorer, grant this service principal **SELECT** and **USE CATALOG** permissions on your target catalog.

#### Step 5: Create the Iceberg Table in Databricks
1. Import the PySpark script `scripts/create_iceberg_inventory.py` into Databricks.
2. Update the script parameters to match your catalog and bucket details if needed.
3. Run the script inside a Databricks Notebook. It will:
   * Create the target catalog and schema if they do not exist.
   * Read the CSV file from `gs://<YOUR_GCS_BUCKET>/raw/inventory.csv`.
   * Rename `stock_level` to `stock_quantity`.
   * Save the dataframe as an Apache Iceberg table on GCS registered in Unity Catalog.

#### Step 6: Setup BigQuery Federation
Run the federation script from your system terminal to register the catalog:
```bash
./scripts/setup_federation.sh
```
* The script will prompt you for the Databricks Service Principal **Client ID** and **Client Secret** created in Step 4.
* It securely writes the credentials into GCP Secret Manager and provisions the BigLake Iceberg federated catalog.
* It binds Secret Accessor roles to BigLake's internal service agent.

---

## Querying the Federated Data in BigQuery

Once the setup is complete, you can query your Databricks-managed Apache Iceberg table directly from BigQuery without moving any data:

```sql
SELECT * FROM `kc-retail-demo`.acme_catalog_fed.raw_data.inventory LIMIT 10;
```
*(Ensure the BigQuery query is run in the same location as your federated catalog setup.)*

---

## Known Issues: Databricks API Deprecation

**Important Note:** As of late 2024, Databricks has officially deprecated the `iceberg/v1/` REST API endpoint in favor of a newer `iceberg-rest/v1/` standard. Currently, Google Cloud BigLake Federation relies on the older `iceberg/v1/` endpoint to fetch metadata.

Because of this version mismatch, BigLake can successfully authenticate and fetch the Databricks schemas, but the subsequent request to fetch tables silently fails. This results in the federated catalog showing 0 tables in BigQuery.

Until Google Cloud updates BigLake to support the `iceberg-rest/v1/` standard, Databricks Unity Catalog Iceberg federation via BigLake may be temporarily broken. In the meantime, you can directly map GCS Delta tables to BigQuery bypassing Unity Catalog entirely.
