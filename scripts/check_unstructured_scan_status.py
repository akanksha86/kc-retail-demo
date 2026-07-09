import os
import requests
import google.auth
from google.auth.transport.requests import Request

def get_access_token():
    credentials, project = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

def check_scan_status():
    token = get_access_token()
    project_id = "kc-retail-demo"
    location = "europe-west1"
    
    # We need the most recent scan ID. 
    # To find it dynamically, we list the DataScans.
    list_url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/dataScans"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(list_url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch DataScans.")
        return
        
    scans = response.json().get("dataScans", [])
    unstructured_scans = [s for s in scans if "unstructured-profile" in s["name"]]
    
    if not unstructured_scans:
        print("No unstructured scans found.")
        return
        
    # Get the latest one
    latest_scan = sorted(unstructured_scans, key=lambda x: x["createTime"], reverse=True)[0]
    scan_name = latest_scan["name"]
    print(f"Latest Scan: {scan_name}")
    
    # List jobs for this scan
    jobs_url = f"https://dataplex.googleapis.com/v1/{scan_name}/jobs"
    jobs_response = requests.get(jobs_url, headers=headers)
    
    jobs = jobs_response.json().get("dataScanJobs", [])
    if not jobs:
        print("No execution jobs found for this scan yet. It may still be starting up.")
        return
        
    latest_job = sorted(jobs, key=lambda x: x.get("startTime", ""), reverse=True)[0]
    
    state = latest_job.get("state", "UNKNOWN")
    print(f"Latest Job Status: {state}")
    
    if state == "SUCCEEDED":
        print("✅ The scan has completed! You should now see the Insights tab populated in Knowledge Catalog.")
    elif state == "RUNNING" or state == "PENDING":
        print("⏳ The scan is still processing. It takes a few minutes to analyze the PDFs using Gemini. Please wait.")
    else:
        print(f"❌ Job finished with state: {state}")
        if "message" in latest_job:
            print(f"Error: {latest_job['message']}")

if __name__ == "__main__":
    check_scan_status()
