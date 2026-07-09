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
gcloud config set project kc-retail-demo
```

---

## Phase 1: Local Dataset & BigQuery Raw Table Loading

The synthetic generator produced 6 highly integrated tables in [`data/`](file:///Users/akankshapb/Antigravity/KC%20Retail%20Demo/data):
* `stores.csv` (23 rows): master store locations (22 physical, 1 online).
* `products.csv` (1,500 rows): retail items with unit prices and unique SKUs.
* `customers.csv` (20,000 rows): global customer demographic profiles.
* `orders.csv` (100,000 rows): customer orders.
* `order_items.csv` (349,016 rows): transactional items mapping orders to products.
* `inventory.csv` (32,752 rows): store inventory snapshots.

### Local Ingestion into BigQuery
To load these files into the project `kc-retail-demo` under dataset `raw_retail_data` in location `EU`:
1. Open your terminal outside the sandbox environment.
2. Run the wrapper script:
   ```bash
   cd "/Users/akankshapb/Antigravity/KC Retail Demo"
   ./scripts/upload.sh
   ```
3. Press **Enter** at the prompts to accept the defaults (`kc-retail-demo` and `raw_retail_data`).

---

## Phase 2: Databricks Unity Catalog & Apache Iceberg Federation

We will create an Apache Iceberg table for the `inventory` dataset on Google Cloud Storage, register it in Databricks Unity Catalog under `acme_catalog.raw_data.inventory`, and federate its metadata to BigQuery.

### Prerequisites & Step-by-Step Setup

#### Step 1: Create the GCS Bucket
Create the regional GCS bucket in `europe-west1` to hold your Iceberg data:
```bash
gcloud storage buckets create gs://kc-retail-demo-warehouse \
  --location=europe-west1 \
  --project=kc-retail-demo
```

#### Step 2: Upload the Raw Inventory Data
Copy the synthetic inventory data to GCS so Databricks can access and process it:
```bash
gcloud storage cp data/inventory.csv gs://kc-retail-demo-warehouse/raw/inventory.csv
```

#### Step 3: Grant Databricks Access to GCS (Storage Credentials)
Configure Databricks Unity Catalog to read and write to the GCS bucket:
1. Log into your Databricks Workspace (`1030582515160828.8.gcp.databricks.com`).
2. Navigate to **Catalog** -> **External Data** -> **Storage Credentials**.
3. Create a Storage Credential. Databricks will generate a GCP Service Account email for this credential.
4. Copy the GCP Service Account email and grant it permissions on your GCS bucket:
   ```bash
   gcloud storage buckets add-iam-policy-binding gs://kc-retail-demo-warehouse \
     --member="serviceAccount:<DATABRICKS_GENERATED_SERVICE_ACCOUNT>" \
     --role="roles/storage.objectAdmin"

   gcloud storage buckets add-iam-policy-binding gs://kc-retail-demo-warehouse \
     --member="serviceAccount:<DATABRICKS_GENERATED_SERVICE_ACCOUNT>" \
     --role="roles/storage.legacyBucketReader"
   ```
5. In Databricks, navigate to **Catalog** -> **External Data** -> **External Locations**.
6. Click **Create Location**, set the URL to `gs://kc-retail-demo-warehouse/`, name it `kc_retail_demo_warehouse`, and select the Storage Credential you created.

#### Step 4: Create a Databricks Service Principal
To allow BigQuery to read metadata from Databricks Unity Catalog, create an OAuth Service Principal:
1. Go to your Databricks Account Console.
2. Navigate to **User Management** -> **Service Principals** and click **Add service principal**.
3. Enter a name (e.g. `bigquery-federation-sp`) and click **Add**.
4. Copy the **Application ID** (this will be your `client_id`).
5. Open the service principal page, go to the **Secrets** tab, click **Generate secret**, and copy the secret value (this will be your `client_secret`).
6. **Assign Permissions**: In the Databricks SQL Editor or Catalog Explorer, grant this service principal **USE CATALOG** on the `acme_catalog` catalog, **USE SCHEMA** on the `raw_data` schema, and **SELECT** privileges on all tables within the `raw_data` schema.
7. **Critical**: You must also grant this service principal **READ FILES** permission on your External Location (`kc_retail_demo_warehouse`). Databricks will hide external tables from the Iceberg API if the service principal doesn't explicitly have access to the underlying storage location.

#### Step 5: Create the Iceberg Table in Databricks
1. Import the PySpark script [`scripts/create_iceberg_inventory.py`](file:///Users/akankshapb/Antigravity/KC%20Retail%20Demo/scripts/create_iceberg_inventory.py) into Databricks.
2. Run the script inside a Databricks Notebook. It will:
   * Create the catalog `acme_catalog` and schema `raw_data` if they do not exist.
   * Read the CSV file from `gs://kc-retail-demo-warehouse/raw/inventory.csv`.
   * Rename `stock_level` to `stock_quantity`.
   * Save the dataframe as an Apache Iceberg table on GCS registered in Unity Catalog.

#### Step 6: Setup BigQuery Federation
Run the federation script from your system terminal to register the catalog:
```bash
./scripts/setup_federation.sh
```
* The script will prompt you for the Databricks Service Principal **Client ID** and **Client Secret** created in Step 4.
* It securely writes the credentials into GCP Secret Manager in the `europe-west1` region and provisions the BigLake Iceberg federated catalog `acme_catalog_fed`.
* It binds Secret Accessor roles to BigLake's internal service agent.

---

## Querying and Writing Federated Data in BigQuery

Once the setup is complete, you can query your Databricks-managed Apache Iceberg table directly from BigQuery without moving any data:

```sql
SELECT * FROM `kc-retail-demo.acme_catalog_fed.raw_data.inventory` LIMIT 10;
```
*(Ensure the BigQuery query is run in the `europe-west1` or `EU` location.)*

### Testing BigQuery Writes to Databricks Iceberg

With the `gcp.biglake.bigquery-dml.enabled` property set on the Iceberg table, you can now write data directly from BigQuery back into the Databricks Unity Catalog managed Iceberg table.

Try inserting a new record:

```sql
INSERT INTO `kc-retail-demo.acme_catalog_fed.raw_data.inventory` (store_id, product_id, stock_quantity, last_updated)
VALUES ('store_999', 'prod_999', 150, CURRENT_TIMESTAMP());
```

You can also update existing records:

```sql
UPDATE `kc-retail-demo.acme_catalog_fed.raw_data.inventory`
SET stock_quantity = stock_quantity + 10
WHERE store_id = 'store_999';
```

*(Note: The BigLake service account requires the `roles/storage.objectAdmin` or `roles/storage.objectUser` role on your GCS bucket to perform writes, which is configured in the federation setup script).*

## Phase 4: Zero-Copy SaaS Federation (Salesforce)

To demonstrate how the Knowledge Catalog integrates CRM data directly alongside your unstructured AI insights and multi-cloud Iceberg catalogs, we simulate a zero-copy federation with Salesforce.

In a production environment, this is achieved natively via **Salesforce Data Cloud's direct BigQuery integration** or **BigQuery Omni**, which projects Salesforce CRM data into BigQuery without ETL pipelines. 

Because we lack a live Salesforce Data Cloud environment, we simulate this federation by generating a synthetic `salesforce_service_cases.csv` and creating a BigQuery External Table over it in Google Cloud Storage.

### Setup Instructions
Run the setup script to generate the synthetic data, upload it to GCS, and create the federated table:
```bash
./scripts/setup_salesforce_federation.sh
```

Once completed, you can query the CRM data seamlessly in BigQuery alongside your other tables:
```sql
SELECT * FROM `kc-retail-demo.raw_retail_data_euw1.salesforce_service_cases` LIMIT 10;
```

## Phase 5: Third-Party Catalog Synchronization (DataHub)

While Dataplex natively crawls GCP resources, many enterprises use tools like DataHub to capture metadata from on-premise databases (Postgres, Oracle) and transformation tools (dbt, Airflow). 

To bring this external metadata into Knowledge Catalog, we establish an event-driven sync. DataHub webhooks trigger a Cloud Function that maps DataHub entities into **Dataplex Custom Aspects**.

### Setup Instructions
Because we don't have a live DataHub instance, we simulate this integration using a mock JSON export (`data/datahub_export.json`) that contains upstream lineage and data quality tiers.

Run the simulation script to see how this metadata is mapped and applied to our BigQuery Dataplex Entries:
```bash
python3 scripts/simulate_datahub_sync.py
```
This script demonstrates the `google-cloud-dataplex` API calls required to attach these Custom Aspects, uniting the enterprise graph.