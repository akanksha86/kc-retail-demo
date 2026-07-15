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
            "type": "string",
            "annotations": {
                "description": "Email address of the primary data owner/steward"
            }
        },
        {
            "name": "department",
            "type": "string",
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
            "type": "boolean",
            "annotations": {
                "description": "Indicates if the dataset contains Personally Identifiable Information"
            }
        }
    ]
    create_aspect_type(token, "retail-contains-pii", "Contains PII (Retail)", "Flags datasets containing PII.", pii_fields)

def attach_aspect_to_entry(token, entry_name, aspect_type, aspect_payload):
    """Attaches a custom aspect to a Dataplex Entry (e.g. BigQuery table)."""
    # Note: Using the Dataplex Catalog API entries endpoint
    print(f"\n--- Attaching {aspect_type} to {entry_name} ---")
    
    # In a real scenario, you'd look up the entry_name using the search API. 
    # The entry name format is: projects/{project}/locations/{location}/entryGroups/{entry_group}/entries/{entry}
    # This is a simulation printing the payload structure required.
    
    payload = {
        "aspects": {
            aspect_type: {
                "aspectType": f"projects/{PROJECT_ID}/locations/{LOCATION}/aspectTypes/{aspect_type}",
                "data": aspect_payload
            }
        }
    }
    
    print(f"API CALL: PATCH https://dataplex.googleapis.com/v1/{entry_name}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("✅ [Simulation] Aspect successfully attached.")

def simulate_create_data_quality_scan(token, scan_id, target_table):
    """Simulates creating a Dataplex DataQualityScan for Retail."""
    print(f"\n--- Creating Data Quality Scan: {scan_id} ---")
    
    payload = {
        "displayName": f"AutoDQ for {target_table}",
        "data": {
            "resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data/tables/{target_table}"
        },
        "dataQualitySpec": {
            "rules": [
                {
                    "column": "stock_quantity",
                    "dimension": "VALIDITY",
                    "rowConditionExpectation": {
                        "sqlExpression": "stock_quantity >= 0"
                    },
                    "description": "Current Stock Level must be non-negative"
                },
                {
                    "column": "unit_price",
                    "dimension": "VALIDITY",
                    "rowConditionExpectation": {
                        "sqlExpression": "unit_price > 0"
                    },
                    "description": "Standard Unit Price must be strictly positive"
                }
            ]
        }
    }
    
    print(f"API CALL: POST https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/dataScans?dataScanId={scan_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("✅ [Simulation] DataQualityScan created.")

def simulate_create_data_product(token, product_id):
    """Simulates creating a Data Product using Dataplex Catalog."""
    print(f"\n--- Creating Data Product: {product_id} ---")
    
    # In Dataplex v1, Data Products are often represented as custom entries in an EntryGroup
    payload = {
        "entryType": "projects/global/locations/global/entryTypes/dataProduct",
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/retail-products/entries/{product_id}",
        "aspects": {
            "retail-data-owner": {
                "aspectType": f"projects/{PROJECT_ID}/locations/{LOCATION}/aspectTypes/retail-data-owner",
                "data": {
                    "owner_email": "marketing-analytics@acme.com",
                    "department": "Marketing"
                }
            },
            "linked_resources": {
                "aspectType": "projects/global/locations/global/aspectTypes/linked_resources",
                "data": {
                    "links": [
                        {"resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data/tables/customers"},
                        {"resource": f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/raw_retail_data/tables/orders"}
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
    
    # 2. Attach Aspects to Tables (Simulation printout to avoid needing hardcoded system entry names)
    attach_aspect_to_entry(
        token, 
        entry_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery/entries/raw_retail_data.customers",
        aspect_type="retail-data-owner",
        aspect_payload={"owner_email": "customer-success@acme.com", "department": "Customer Success"}
    )
    
    attach_aspect_to_entry(
        token, 
        entry_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery/entries/raw_retail_data.customers",
        aspect_type="retail-contains-pii",
        aspect_payload={"has_pii": True}
    )
    
    # 3. Create Data Quality Scan (Simulation)
    simulate_create_data_quality_scan(token, "inventory-dq-scan", "inventory")
    simulate_create_data_quality_scan(token, "products-dq-scan", "products")
    
    # 4. Create Data Product (Simulation)
    simulate_create_data_product(token, "acme_customer_360_insights")
    
    print("\n=================================================")
    print("Metadata Enrichment Scripts Completed.")
    print("=================================================")

if __name__ == "__main__":
    main()
