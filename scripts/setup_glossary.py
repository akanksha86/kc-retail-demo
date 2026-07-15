import google.auth
from google.auth.transport.requests import Request
import requests

PROJECT_ID = "kc-retail-demo"
LOCATION = "europe-west1"
GLOSSARY_ID = "retail-business-glossary"

def get_access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

def create_glossary(token):
    url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/glossaries?glossaryId={GLOSSARY_ID}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "displayName": "Retail Business Glossary",
        "description": "Core business concepts for Acme Retail"
    }
    print(f"Creating Glossary: {GLOSSARY_ID}...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Glossary '{GLOSSARY_ID}' created successfully.")
    elif response.status_code == 409:
        print(f"ℹ️ Glossary '{GLOSSARY_ID}' already exists.")
    else:
        print(f"❌ Failed to create Glossary. Status: {response.status_code}")
        print(response.text)

def create_term(token, term_id, display_name):
    url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}/terms?termId={term_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "parent": f"projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}",
        "displayName": display_name
    }
    print(f"Creating Term: {term_id} ({display_name})...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  ✅ Term '{term_id}' created successfully.")
    elif response.status_code == 409:
        print(f"  ℹ️ Term '{term_id}' already exists.")
    else:
        print(f"  ❌ Failed to create Term. Status: {response.status_code}")
        print(response.text)

def main():
    print("=================================================")
    print("Setting up Retail Business Glossary")
    print("=================================================")
    token = get_access_token()
    
    create_glossary(token)
    
    terms = [
        ("customer-loyalty-index", "Customer Loyalty Index"),
        ("contact-email-address", "Contact Email Address"),
        ("total-order-revenue", "Total Order Revenue"),
        ("standard-unit-price", "Standard Unit Price"),
        ("stock-keeping-unit", "Stock Keeping Unit (SKU)"),
        ("current-stock-level", "Current Stock Level"),
        ("inventory-snapshot-time", "Inventory Snapshot Time"),
        ("retail-branch-name", "Retail Branch Name"),
    ]
    
    for term_id, display_name in terms:
        create_term(token, term_id, display_name)
        
    print("\nGlossary setup complete!")

if __name__ == "__main__":
    main()
