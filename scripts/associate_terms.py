import json
import requests
import google.auth
from google.auth.transport.requests import Request

PROJECT_ID = "kc-retail-demo"
LOCATION = "europe-west1"
DATASET_ID = "raw_retail_data_euw1"
GLOSSARY_ID = "retail-business-glossary"

MAPPINGS = {
    "customers": {
        "customer_segment": "customer-loyalty-index",
        "email": "contact-email-address"
    },
    "orders": {
        "total_amount": "total-order-revenue"
    },
    "products": {
        "unit_price": "standard-unit-price",
        "sku": "stock-keeping-unit"
    },
    "inventory": {
        "stock_level": "current-stock-level",
        "last_updated": "inventory-snapshot-time"
    },
    "stores": {
        "store_name": "retail-branch-name"
    }
}

def get_access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

def create_entry_link(token, table_id, column_name, term_id):
    term_resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}/terms/{term_id}"
    term_entry_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@dataplex/entries/{term_resource_name}"
    
    bq_entry_id = f"bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables/{table_id}"
    table_entry_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery/entries/{bq_entry_id}"
    
    parent_group = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery"
    
    clean_column = column_name.replace("_", "-").lower()
    clean_table = table_id.replace("_", "-").lower()
    entry_link_id = f"link-{clean_table}-{clean_column}"
    
    url = f"https://dataplex.googleapis.com/v1/{parent_group}/entryLinks?entryLinkId={entry_link_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "entryLinkType": "projects/dataplex-types/locations/global/entryLinkTypes/definition",
        "entryReferences": [
            {
                "name": table_entry_name,
                "path": f"Schema.{column_name}",
                "type": "SOURCE"
            },
            {
                "name": term_entry_name,
                "type": "TARGET"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Successfully linked {table_id}.{column_name} -> Term '{term_id}'")
        return True
    elif response.status_code == 409:
        print(f"ℹ️ Link already exists for {table_id}.{column_name}")
        return True
    elif response.status_code == 400 and "not found" in response.text.lower():
        print(f"⚠️ Term entry not found using project ID. Retrying with project number.")
        return False
    else:
        print(f"❌ Failed to link {table_id}.{column_name}. Status: {response.status_code}")
        print(response.text)
        return False

def get_project_number(token):
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{PROJECT_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("projectNumber")
    return None

def create_entry_link_with_project_number(token, table_id, column_name, term_id, project_number):
    term_resource_name = f"projects/{project_number}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}/terms/{term_id}"
    term_entry_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@dataplex/entries/{term_resource_name}"
    
    bq_entry_id = f"bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables/{table_id}"
    table_entry_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery/entries/{bq_entry_id}"
    
    parent_group = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/@bigquery"
    
    clean_column = column_name.replace("_", "-").lower()
    clean_table = table_id.replace("_", "-").lower()
    entry_link_id = f"link-{clean_table}-{clean_column}"
    
    url = f"https://dataplex.googleapis.com/v1/{parent_group}/entryLinks?entryLinkId={entry_link_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "entryLinkType": "projects/dataplex-types/locations/global/entryLinkTypes/definition",
        "entryReferences": [
            {
                "name": table_entry_name,
                "path": f"Schema.{column_name}",
                "type": "SOURCE"
            },
            {
                "name": term_entry_name,
                "type": "TARGET"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  ✅ Successfully linked {table_id}.{column_name} -> Term '{term_id}' (via Project Number)")
    elif response.status_code == 409:
        print(f"  ℹ️ Link already exists for {table_id}.{column_name}")
    else:
        print(f"  ❌ Failed to link {table_id}.{column_name} via Project Number. Status: {response.status_code}")
        print(response.text)

def main():
    print("=================================================")
    print("Associating Business Glossary Terms via Dataplex EntryLinks")
    print("=================================================")
    token = get_access_token()
    project_number = None

    for table_name, columns in MAPPINGS.items():
        print(f"Processing table: {table_name}")
        for column_name, term_id in columns.items():
            success = create_entry_link(token, table_name, column_name, term_id)
            if not success:
                if project_number is None:
                    project_number = get_project_number(token)
                if project_number:
                    create_entry_link_with_project_number(token, table_name, column_name, term_id, project_number)

if __name__ == "__main__":
    main()
