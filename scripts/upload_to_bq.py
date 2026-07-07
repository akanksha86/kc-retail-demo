#!/usr/bin/env python3
import argparse
import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Define schemas for BigQuery tables to ensure correct data types
SCHEMAS = {
    "stores": [
        bigquery.SchemaField("store_id", "STRING", mode="REQUIRED", description="Unique store identifier"),
        bigquery.SchemaField("store_name", "STRING", mode="NULLABLE", description="Full name of the store location"),
        bigquery.SchemaField("location", "STRING", mode="NULLABLE", description="Street address of the store"),
        bigquery.SchemaField("region", "STRING", mode="NULLABLE", description="State or province"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE", description="Country name")
    ],
    "products": [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED", description="Unique product identifier"),
        bigquery.SchemaField("product_name", "STRING", mode="NULLABLE", description="Name of the product"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE", description="Detailed product description"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE", description="Product category group"),
        bigquery.SchemaField("brand", "STRING", mode="NULLABLE", description="Brand or manufacturer"),
        bigquery.SchemaField("unit_price", "NUMERIC", mode="NULLABLE", description="Price per single unit"),
        bigquery.SchemaField("sku", "STRING", mode="NULLABLE", description="Stock Keeping Unit code"),
        bigquery.SchemaField("is_active", "BOOLEAN", mode="NULLABLE", description="Is product currently active/sold")
    ],
    "customers": [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", description="Unique customer identifier"),
        bigquery.SchemaField("first_name", "STRING", mode="NULLABLE", description="Customer's first name"),
        bigquery.SchemaField("last_name", "STRING", mode="NULLABLE", description="Customer's last name"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE", description="Email address"),
        bigquery.SchemaField("phone", "STRING", mode="NULLABLE", description="Phone number with country code"),
        bigquery.SchemaField("address", "STRING", mode="NULLABLE", description="Street address"),
        bigquery.SchemaField("city", "STRING", mode="NULLABLE", description="City name"),
        bigquery.SchemaField("state", "STRING", mode="NULLABLE", description="State or province"),
        bigquery.SchemaField("zip_code", "STRING", mode="NULLABLE", description="Postal/ZIP code"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE", description="Country code/name"),
        bigquery.SchemaField("registration_date", "DATE", mode="NULLABLE", description="Date when user registered"),
        bigquery.SchemaField("customer_segment", "STRING", mode="NULLABLE", description="Segment class (VIP, Regular, New)")
    ],
    "orders": [
        bigquery.SchemaField("order_id", "STRING", mode="REQUIRED", description="Unique order identifier"),
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", description="Foreign key reference to Customers"),
        bigquery.SchemaField("store_id", "STRING", mode="NULLABLE", description="Foreign key reference to Stores"),
        bigquery.SchemaField("order_date", "DATE", mode="NULLABLE", description="Date order was placed"),
        bigquery.SchemaField("order_status", "STRING", mode="NULLABLE", description="Status (Delivered, Shipped, Pending, Cancelled)"),
        bigquery.SchemaField("shipping_address", "STRING", mode="NULLABLE", description="Shipping street address"),
        bigquery.SchemaField("shipping_city", "STRING", mode="NULLABLE", description="Shipping city"),
        bigquery.SchemaField("shipping_state", "STRING", mode="NULLABLE", description="Shipping state/province"),
        bigquery.SchemaField("shipping_zip", "STRING", mode="NULLABLE", description="Shipping ZIP/Postal code"),
        bigquery.SchemaField("shipping_country", "STRING", mode="NULLABLE", description="Shipping country"),
        bigquery.SchemaField("total_amount", "NUMERIC", mode="NULLABLE", description="Total order value sum")
    ],
    "order_items": [
        bigquery.SchemaField("order_item_id", "STRING", mode="REQUIRED", description="Unique order item identifier"),
        bigquery.SchemaField("order_id", "STRING", mode="REQUIRED", description="Foreign key reference to Orders"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED", description="Foreign key reference to Products"),
        bigquery.SchemaField("quantity", "INTEGER", mode="NULLABLE", description="Quantity purchased"),
        bigquery.SchemaField("price_per_unit", "NUMERIC", mode="NULLABLE", description="Selling price per unit at order time")
    ],
    "inventory": [
        bigquery.SchemaField("inventory_id", "STRING", mode="REQUIRED", description="Unique inventory level identifier"),
        bigquery.SchemaField("store_id", "STRING", mode="REQUIRED", description="Foreign key reference to Stores"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED", description="Foreign key reference to Products"),
        bigquery.SchemaField("stock_level", "INTEGER", mode="NULLABLE", description="Current quantity in stock"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="NULLABLE", description="Timestamp of last stock count refresh")
    ]
}

def upload_csv_to_bq(client, dataset_ref, table_name, csv_path):
    print(f"Uploading {csv_path} to table {dataset_ref.table(table_name)}...")
    
    table_ref = dataset_ref.table(table_name)
    
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMAS[table_name],
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    with open(csv_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
        
    job.result()  # Wait for the load job to complete.
    
    # Reload table to verify row count
    table = client.get_table(table_ref)
    print(f"Successfully uploaded. Loaded {table.num_rows} rows into {table_ref.path}.")

def main():
    parser = argparse.ArgumentParser(description="Upload synthetic retail CSV files to BigQuery.")
    parser.add_argument("--project_id", help="Google Cloud project ID (optional, defaults to active gcloud config)")
    parser.add_argument("--dataset_id", default="raw_retail_data", help="Destination BigQuery dataset ID (default: raw_retail_data)")
    parser.add_argument("--location", default="US", help="BigQuery dataset location (default: US)")
    
    args = parser.parse_args()
    
    # Initialize BigQuery client
    client = bigquery.Client(project=args.project_id) if args.project_id else bigquery.Client()
    project = client.project
    
    dataset_ref = bigquery.DatasetReference(project, args.dataset_id)
    
    # Create dataset if it does not exist
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{project}.{args.dataset_id}' already exists.")
    except NotFound:
        print(f"Dataset '{project}.{args.dataset_id}' not found. Creating in location '{args.location}'...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = args.location
        dataset.description = "Synthetic retail dataset for Acme Retail demo context"
        client.create_dataset(dataset)
        print(f"Created dataset '{project}.{args.dataset_id}' in {args.location}.")
        
    # Get current directory data files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory '{data_dir}' does not exist. Please run scripts/generate_data.py first.")
        return
        
    files = {
        "stores": os.path.join(data_dir, "stores.csv"),
        "products": os.path.join(data_dir, "products.csv"),
        "customers": os.path.join(data_dir, "customers.csv"),
        "orders": os.path.join(data_dir, "orders.csv"),
        "order_items": os.path.join(data_dir, "order_items.csv"),
        "inventory": os.path.join(data_dir, "inventory.csv")
    }
    
    # Perform upload
    for table_name, csv_path in files.items():
        if os.path.exists(csv_path):
            try:
                upload_csv_to_bq(client, dataset_ref, table_name, csv_path)
            except Exception as e:
                print(f"Error uploading {table_name}: {e}")
        else:
            print(f"Warning: File not found: {csv_path}. Skipping.")
            
    print("\nAll uploads completed!")

if __name__ == "__main__":
    main()
