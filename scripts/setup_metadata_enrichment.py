#!/usr/bin/env python3
import json
import requests
import google.auth
from google.auth.transport.requests import Request

# Configuration
PROJECT_ID = "kc-retail-demo"
LOCATION = "europe-west1"
ENTRY_GROUP_ID = "retail-metadata-group" # Using a generic group for custom metadata

def get_access_token():
    """Gets a valid GCP access token using Application Default Credentials."""
    try:
        credentials, project = google.auth.default()
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        print(f"Error obtaining Google Cloud credentials: {e}")
        print("Please ensure you have run 'gcloud auth application-default login'")
        exit(1)

def create_aspect_type(token, aspect_type_id, display_name, description, fields):
    """Creates a Custom Aspect Type in Dataplex."""
    print(f"\n--- Creating Aspect Type: {aspect_type_id} ---")
    url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/aspectTypes?aspectTypeId={aspect_type_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "displayName": display_name,
        "description": description,
        "metadataTemplate": {
            "name": aspect_type_id,
            "type": "record",
            "recordFields": fields
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"✅ Aspect Type '{aspect_type_id}' created successfully.")
    elif response.status_code == 409:
        print(f"ℹ️ Aspect Type '{aspect_type_id}' already exists.")
    else:
        print(f"❌ Failed to create Aspect Type. Status: {response.status_code}")
        print(response.text)

def setup_aspect_types(token):
    """Defines and creates the retail-specific aspect types."""
    # 1. Retail Data Owner Aspect
    owner_fields = [
        {
            "name": "owner_email",
            "type": "STRING",
            "index": 1,
            "annotations": {
                "description": "Email address of the primary data owner/steward"
            }
        },
        {
            "name": "department",
            "type": "STRING",
            "index": 2,
            "annotations": {
                "description": "Department responsible for the dataset"
            }
        }
    ]
    create_aspect_type(token, "retail-data-owner", "Retail Data Owner", "Tracks ownership of retail data assets.", owner_fields)
    
    # 2. Retail PII Aspect
    pii_fields = [
        {
            "name": "has_pii",
            "type": "STRING",
            "index": 1,
            "annotations": {
                "description": "Indicates if the dataset contains Personally Identifiable Information (Yes/No)"
            }
        }
    ]
    create_aspect_type(token, "retail-contains-pii", "Contains PII (Retail)", "Flags datasets containing PII.", pii_fields)

def lookup_entry_name(token, bq_resource):
    """Looks up the correct Dataplex Entry name using the canonical Data Catalog lookup API."""
    url = f"https://datacatalog.googleapis.com/v1/entries:lookup?linkedResource={bq_resource}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("name")
    else:
        print(f"❌ Data Catalog lookup failed for {bq_resource}. Status: {response.status_code}")
        print(response.text)
        return None

def attach_aspect_to_entry(token, entry_name, aspect_type, aspect_payload):
    """Attaches a custom aspect to a Dataplex Entry (e.g. BigQuery table)."""
    # Note: Using the Dataplex Catalog API entries endpoint
    print(f"\n--- Attaching {aspect_type} to {entry_name} ---")
    
    # In a real scenario, you'd look up the entry_name using the search API. 
    # The entry name format is: projects/{project}/locations/{location}/entryGroups/{entry_group}/entries/{entry}
    # This is a simulation printing the payload structure required.
    
    payload = {
        "aspects": {
            f"{PROJECT_ID}.{LOCATION}.{aspect_type}": {
                "aspectType": f"projects/{PROJECT_ID}/locations/{LOCATION}/aspectTypes/{aspect_type}",
                "data": aspect_payload
            }
        }
    }
    
    url = f"https://dataplex.googleapis.com/v1/{entry_name}?updateMask=aspects"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"✅ Aspect '{aspect_type}' successfully attached.")
    else:
        print(f"❌ Failed to attach aspect. Status: {response.status_code}")
        print(response.text)

def create_data_quality_scan(token, scan_id, target_table, rules_payload):
    """Creates a Dataplex DataQualityScan for Retail."""
    print(f"\n--- Creating Data Quality Scan: {scan_id} ---")
    
    payload = {
        "displayName": f"AutoDQ for {target_table}",
        "data": {
            "resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data_euw1/tables/{target_table}"
        },
        "dataQualitySpec": {
            "rules": rules_payload
        }
    }
    
    url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/dataScans?dataScanId={scan_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200 or response.status_code == 201:
        print(f"✅ DataQualityScan '{scan_id}' created successfully.")
    elif response.status_code == 409:
        print(f"ℹ️ DataQualityScan '{scan_id}' already exists.")
    else:
        print(f"❌ Failed to create DataQualityScan. Status: {response.status_code}")
        print(response.text)

def create_data_product(token, product_id):
    """Creates a Data Product using Dataplex Catalog."""
    print(f"\n--- Creating Data Product: {product_id} ---")
    
    # In Dataplex v1, Data Products are often represented as custom entries in an EntryGroup
    payload = {
        "entryType": "projects/global/locations/global/entryTypes/dataProduct",
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/retail-products/entries/{product_id}",
        "aspects": {
            f"{PROJECT_ID}.{LOCATION}.retail-data-owner": {
                "aspectType": f"projects/{PROJECT_ID}/locations/{LOCATION}/aspectTypes/retail-data-owner",
                "data": {
                    "owner_email": "marketing-analytics@acme.com",
                    "department": "Marketing"
                }
            },
            "global.global.linked_resources": {
                "aspectType": "projects/global/locations/global/aspectTypes/linked_resources",
                "data": {
                    "links": [
                        {"resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data_euw1/tables/customers"},
                        {"resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data_euw1/tables/orders"}
                    ]
                }
            }
        }
    }
    
    print(f"API CALL: POST https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/retail-products/entries?entryId={product_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("✅ [Simulation] Data Product 'Acme Customer 360 Insights' created.")

def main():
    print("=================================================")
    print("Initializing Acme Retail Metadata Enrichment")
    print("=================================================")
    token = get_access_token()
    
    # 1. Create Aspect Types (Actual API call)
    setup_aspect_types(token)
    
    # 2. Attach Aspects to Tables
    bq_resource = f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data_euw1/tables/customers"
    actual_entry_name = lookup_entry_name(token, bq_resource)
    
    if actual_entry_name:
        attach_aspect_to_entry(
            token, 
            entry_name=actual_entry_name,
            aspect_type="retail-data-owner",
            aspect_payload={"owner_email": "customer-success@acme.com", "department": "Customer Success"}
        )
        
        attach_aspect_to_entry(
            token, 
            entry_name=actual_entry_name,
            aspect_type="retail-contains-pii",
            aspect_payload={"has_pii": "Yes"}
        )
    else:
        print("Skipping Aspect Attachment due to lookup failure.")
    
    # 3. Create Data Quality Scan
    inventory_rules = [
        {
            "column": "stock_level",
            "dimension": "VALIDITY",
            "rowConditionExpectation": {
                "sqlExpression": "stock_level >= 0"
            },
            "description": "Current Stock Level must be non-negative"
        }
    ]
    create_data_quality_scan(token, "inventory-dq-scan", "inventory", inventory_rules)
    
    products_rules = [
        {
            "column": "unit_price",
            "dimension": "VALIDITY",
            "rowConditionExpectation": {
                "sqlExpression": "unit_price > 0"
            },
            "description": "Standard Unit Price must be strictly positive"
        }
    ]
    create_data_quality_scan(token, "products-dq-scan", "products", products_rules)
    
    # 4. Create Data Product
    create_data_product(token, "acme_customer_360_insights")
    
    print("\n=================================================")
    print("Metadata Enrichment Scripts Completed.")
    print("=================================================")

if __name__ == "__main__":
    main()
