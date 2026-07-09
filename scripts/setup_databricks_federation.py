#!/usr/bin/env python3
import json
import os
import time
import subprocess

PROJECT_ID = "kc-retail-demo"

# Secret Manager regional secrets and BigLake federated catalogs must be placed in a specific GCP region, 
# not a multi-region like 'EU'. 'europe-west4' (Eemshaven, Netherlands) is the standard GCP region for EU workloads.
REGION = "europe-west4" 

CATALOG_NAME = "databricks_federated"
DATABRICKS_WORKSPACE = "1030582515160828.8.gcp.databricks.com"
DATABRICKS_CATALOG = "acme_catalog"
SECRET_NAME = "databricks-oauth-creds"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

def run_cmd(cmd, capture_output=False):
    print(f"Running: {cmd}")
    if capture_output:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    else:
        subprocess.run(cmd, shell=True, check=True)

def main():
    print("=====================================================")
    print("Setting up Databricks Unity Catalog Federation in BQ")
    print("=====================================================")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: {CREDENTIALS_FILE} not found!")
        return

    print("1. Creating Regional Secret in Secret Manager...")
    # Set the regional API endpoint for Secret Manager
    run_cmd(f"gcloud config set api_endpoint_overrides/secretmanager https://secretmanager.{REGION}.rep.googleapis.com/")
    
    try:
        try:
            run_cmd(f"gcloud secrets describe {SECRET_NAME} --project={PROJECT_ID} --location={REGION}")
            print("Secret already exists. Updating it...")
            run_cmd(f"gcloud secrets versions add {SECRET_NAME} --project={PROJECT_ID} --location={REGION} --data-file='{CREDENTIALS_FILE}'")
        except subprocess.CalledProcessError:
            print("Creating new secret...")
            run_cmd(f"gcloud secrets create {SECRET_NAME} --project={PROJECT_ID} --location={REGION} --data-file='{CREDENTIALS_FILE}'")
            
        print("\n2. Creating BigLake Federated Catalog for Databricks...")
        try:
            run_cmd(f"gcloud alpha biglake iceberg catalogs describe {CATALOG_NAME} --project={PROJECT_ID}")
            print("Catalog already exists.")
        except subprocess.CalledProcessError:
            run_cmd(f'''gcloud alpha biglake iceberg catalogs create {CATALOG_NAME} \\
                --project="{PROJECT_ID}" \\
                --primary-location="{REGION}" \\
                --catalog-type="federated" \\
                --federated-catalog-type="unity" \\
                --secret-name="projects/{PROJECT_ID}/locations/{REGION}/secrets/{SECRET_NAME}" \\
                --unity-instance-name="{DATABRICKS_WORKSPACE}" \\
                --unity-catalog-name="{DATABRICKS_CATALOG}" \\
                --refresh-interval="300s"''')

        print("\n3. Granting Catalog Service Account access to Secret...")
        sa_email = run_cmd(f'gcloud alpha biglake iceberg catalogs describe {CATALOG_NAME} --project="{PROJECT_ID}" --format="value(biglake-service-account)"', capture_output=True)
        print(f"Service Account: {sa_email}")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                run_cmd(f'gcloud secrets add-iam-policy-binding {SECRET_NAME} --project="{PROJECT_ID}" --location="{REGION}" --member="serviceAccount:{sa_email}" --role="roles/secretmanager.secretAccessor"')
                break
            except subprocess.CalledProcessError:
                if attempt < max_retries - 1:
                    print(f"Service Account not ready yet (IAM propagation delay). Retrying in 10s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(10)
                else:
                    raise

        print("\n4. Triggering catalog refresh and checking for tables...")
        # Force a refresh to happen immediately now that IAM is correct
        run_cmd(f'gcloud alpha biglake iceberg catalogs update {CATALOG_NAME} --project="{PROJECT_ID}" --refresh-interval="300s"')
        
        print("Waiting 15 seconds for Databricks metadata sync...")
        time.sleep(15) 
        
        try:
            output = run_cmd(f'bq ls --location={REGION} {PROJECT_ID}:{CATALOG_NAME}', capture_output=True)
            if "Not found" in output or output.strip() == "":
                print("\nWARNING: No schemas found in the federated catalog.")
            else:
                print("\nSUCCESS! Found the following federated schemas:")
                print(output)
                
                # Check tables inside the first schema found (assuming 'main' or 'default')
                print(f"\nChecking tables inside {PROJECT_ID}:{CATALOG_NAME}.raw_data...")
                tables_output = run_cmd(f'bq ls --location={REGION} {PROJECT_ID}:{CATALOG_NAME}.raw_data', capture_output=True)
                print(tables_output)
                
        except Exception as e:
            print(f"\nError querying catalog via bq ls: {e}")

        print("=====================================================")

    finally:
        # Unset the override so we don't break other tools
        run_cmd("gcloud config unset api_endpoint_overrides/secretmanager")

if __name__ == "__main__":
    main()

