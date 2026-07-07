#!/usr/bin/env python3
"""
Databricks PySpark Script: Create Iceberg Inventory Table

Instructions:
1. Upload this script to a Databricks Notebook or run it as a Databricks Job.
2. Ensure your Databricks cluster has read/write access to the Google Cloud Storage bucket
   `gs://kc-retail-demo-warehouse` (configured via Unity Catalog Storage Credentials & External Locations).
3. Upload the generated local `data/inventory.csv` file to GCS at:
   `gs://kc-retail-demo-warehouse/raw/inventory.csv`
4. Run this script in Databricks to create and register the Iceberg table in Unity Catalog.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

def main():
    # Initialize Spark Session (not strictly necessary inside Databricks notebooks, but good practice)
    spark = SparkSession.builder \
        .appName("Create Iceberg Inventory Table") \
        .getOrCreate()

    # Define paths and names
    gcs_csv_path = "gs://kc-retail-demo-warehouse/raw/inventory.csv"
    gcs_iceberg_location = "gs://kc-retail-demo-warehouse/inventory_uniform"
    
    catalog_name = "acme_catalog"
    schema_name = "raw_data"
    table_name = "inventory"
    full_table_path = f"{catalog_name}.{schema_name}.{table_name}"

    print(f"Creating catalog '{catalog_name}' and schema '{schema_name}' if they don't exist...")
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog_name} MANAGED LOCATION 'gs://kc-retail-demo-warehouse/metastore/'")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

    print(f"Reading raw inventory CSV from: {gcs_csv_path}")
    # Read the synthetic CSV data
    inventory_df = spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .load(gcs_csv_path)

    print("Re-structuring columns to match requested Iceberg schema...")
    # Rename stock_level to stock_quantity and drop the inventory_id column (not in requested schema)
    # The requested schema is: store_id, product_id, stock_quantity, last_updated
    iceberg_df = inventory_df \
        .withColumnRenamed("stock_level", "stock_quantity") \
        .select("store_id", "product_id", "stock_quantity", "last_updated")

    print(f"Dropping existing Iceberg table '{full_table_path}' to replace with Delta...")
    spark.sql(f"DROP TABLE IF EXISTS {full_table_path}")

    print(f"Creating Delta UniForm table at {gcs_iceberg_location} and registering in Unity Catalog...")
    
    # Use DataFrame V2 API to create the table with TBLPROPERTIES from the start!
    # This ensures Databricks generates the Iceberg metadata automatically on the first write.
    iceberg_df.writeTo(full_table_path) \
        .tableProperty("delta.enableDeletionVectors", "false") \
        .tableProperty("delta.columnMapping.mode", "name") \
        .tableProperty("delta.universalFormat.enabledFormats", "iceberg") \
        .tableProperty("delta.enableIcebergCompatV2", "true") \
        .using("delta") \
        .createOrReplace()

    print(f"Verification: Reading data back from Unity Catalog ({full_table_path})...")
    verify_df = spark.read.table(full_table_path)
    verify_df.show(5)
    print(f"Successfully registered Iceberg table. Total rows: {verify_df.count()}")

if __name__ == "__main__":
    main()
