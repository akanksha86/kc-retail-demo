import os
import json
import requests
import google.auth
from google.auth.transport.requests import Request
import time

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

def trigger_dataplex_unstructured_scan():
    token = get_access_token()
    
    project_id = "kc-retail-demo"
    location = "europe-west1"  
    dataset_id = "raw_retail_data_euw1"
    table_id = "unstructured_docs"
    
    # Generate a unique scan ID based on timestamp to avoid conflicts if run multiple times
    scan_id = f"unstructured-profile-{int(time.time())}"

    print(f"=================================================")
    print(f"Creating Dataplex Unstructured Data Profile Scan")
    print(f"Scan ID: {scan_id}")
    print(f"Target: BigQuery Object Table ({project_id}.{dataset_id}.{table_id})")
    print(f"=================================================")

    create_url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/dataScans?dataScanId={scan_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Payload for unstructured data profile scan
    # It targets the BigQuery Object table that holds references to our PDFs
    payload = {
        "displayName": "Retail Manuals Unstructured Profile",
        "description": "Profiles PDF manuals to extract semantic insights and graph relationships.",
        "data": {
            "resource": f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
        },
        "unstructuredDataProfileSpec": {
            "graphProfilePublishingEnabled": True,
            "customizedPrompt": "Extract the following retail entity nodes from these manuals: Product Name, Product ID, Store ID, Brand, and Warranty Period."
        }
    }
    
    print("Sending API request to create the scan...")
    response = requests.post(create_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        resp_json = response.json()
        print(f"✅ Creation request accepted: {scan_id}\n")
        
        if "name" in resp_json and "/operations/" in resp_json["name"]:
            operation_name = resp_json["name"]
            print(f"Waiting for creation operation to complete: {operation_name}")
            while True:
                op_url = f"https://dataplex.googleapis.com/v1/{operation_name}"
                op_response = requests.get(op_url, headers=headers)
                op_json = op_response.json()
                if op_json.get("done"):
                    if "error" in op_json:
                        print(f"❌ Operation failed: {op_json['error']}")
                        return
                    print("✅ DataScan fully created on backend!")
                    break
                print("Still creating... waiting 5 seconds.")
                time.sleep(5)
        
        # Once created, trigger a run
        print(f"Triggering execution for the scan...")
        run_url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/dataScans/{scan_id}:run"
        run_response = requests.post(run_url, headers=headers)
        
        if run_response.status_code == 200:
            print(f"✅ Successfully triggered scan execution!")
            print(f"Raw Job details from API: {run_response.json()}")
            print(f"The scanning process is now running in the background.")
        else:
            print(f"❌ Failed to trigger scan execution. Status Code: {run_response.status_code}")
            print(run_response.text)
    else:
        print(f"❌ Failed to create DataScan. Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    trigger_dataplex_unstructured_scan()
