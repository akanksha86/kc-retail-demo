import json
import os

print("=================================================")
print("Simulating DataHub to Dataplex Synchronization...")
print("=================================================")
print("In a production environment, this is handled entirely by DataHub Cloud's")
print("native 'Knowledge Catalog Metadata Sync' Automation.")
print("It uses the google-cloud-dataplex API to upsert Custom Aspects.")
print("=================================================\n")

export_path = 'data/datahub_export.json'

if not os.path.exists(export_path):
    print(f"Error: Could not find DataHub export at {export_path}")
    exit(1)

with open(export_path, 'r') as f:
    datahub_payload = json.load(f)

print(f"Received DataHub Export (v{datahub_payload.get('export_version')}) at {datahub_payload.get('exported_at')}")
print(f"Processing {len(datahub_payload.get('entities', []))} entities...\n")

for entity in datahub_payload.get('entities', []):
    bq_table = entity['target_bq_table']
    urn = entity['datahub_urn']
    dq = entity['data_quality']
    steward = entity['steward']
    domain = entity['domain']
    
    print(f"--> Target BigQuery Asset: {bq_table}")
    print(f"    1. Mapping DataHub URN: {urn}")
    print(f"    2. Resolving Dataplex Entry ID for {bq_table}...")
    
    # Simulate API Call
    print(f"    3. API CALL: DataplexClient.update_aspect(")
    print(f"         entry_name='projects/kc-retail-demo/locations/europe-west1/entryGroups/...',")
    print(f"         aspect_type='datahub_integration_aspect',")
    print(f"         aspect={{")
    print(f"             'data_quality_tier': '{dq['tier']}',")
    print(f"             'dbt_test_status': '{dq['last_dbt_test_run']}',")
    print(f"             'data_steward': '{steward}',")
    print(f"             'business_domain': '{domain}',")
    print(f"             'upstream_sources': {entity['upstream_lineage']}")
    print(f"         }}")
    print(f"       )")
    print("    [SUCCESS] Custom Aspect attached to Dataplex Entry.\n")

print("=================================================")
print("Sync Complete! DataHub lineage and quality scores are now")
print("searchable natively in Google Cloud Knowledge Catalog.")
print("=================================================")
