# Dataplex Data Governance & Metadata Guide (Retail)

This guide outlines the data governance structure, manual metadata mappings, recommended Data Quality rules, and Data Product topologies for the Acme Retail environment.

## 1. Metadata Mapping (Aspects & Glossary)

*Attach Aspects via Knowledge Catalog > Entries > Attach Aspect.*
*Attach Glossary Terms via Knowledge Catalog > Entries > Schema Tab > Attach Glossary Term.*

### Core Tables
| BigQuery Table | Custom Aspect Type to Attach | Data to enter in UI | Glossary Terms (Column Level) |
| :--- | :--- | :--- | :--- |
| **`customers`** | `retail-data-owner` | `customer-success@acme.com` | `customer_segment` -> **Customer Loyalty Index** <br> `email` -> **Contact Email Address** |
| | `retail-contains-pii` | `True` | |
| **`orders`** | `retail-data-owner` | `sales-ops@acme.com` | `total_amount` -> **Total Order Revenue** |
| | `retail-contains-pii` | `True` | |
| **`products`** | `retail-data-owner` | `merchandising@acme.com` | `unit_price` -> **Standard Unit Price** <br> `sku` -> **Stock Keeping Unit (SKU)** |
| | `retail-contains-pii` | `False` | |
| **`inventory`** | `retail-data-owner` | `supply-chain@acme.com` | `stock_level` -> **Current Stock Level** <br> `last_updated` -> **Inventory Snapshot Time** |
| | `retail-contains-pii` | `False` | |
| **`stores`** | `retail-data-owner` | `retail-ops@acme.com` | `store_name` -> **Retail Branch Name** |
| | `retail-contains-pii` | `False` | |

### Aggregated / Unified Views
| BigQuery Table | Custom Aspect Type to Attach | Data to enter in UI | Glossary Terms (Column Level) |
| :--- | :--- | :--- | :--- |
| **`customer_360_view`** | `retail-data-owner` | `marketing-analytics@acme.com` | Inherits from underlying columns |
| | `retail-contains-pii` | `True` | |
| **`unified_inventory_view`** | `retail-data-owner` | `supply-chain@acme.com` | Inherits from underlying columns |
| | `retail-contains-pii` | `False` | |

---

## 2. Architecture Recommendation: Cross-Cloud Lakehouse Federation

**How should federated Databricks Iceberg inventory data be integrated with native BigQuery order data?**
* **Via Zero-Copy Logical Views.** The core transaction tables (`orders` and `order_items`) reside natively in BigQuery, while the `inventory` dataset is managed by Databricks Unity Catalog as an Apache Iceberg table on Google Cloud Storage. Moving data back and forth for every query is fragile and expensive.
* **Best Practice**: Create a unified **BigQuery View** (e.g., `unified_inventory_view`) that performs a live `JOIN` between the native BigQuery `products` table and the federated Databricks Iceberg `inventory` table (accessed via BigLake). This allows the Conversational Agent to seamlessly query current stock availability without any ETL data movement.

---

## 3. Recommended Data Quality Rules (AutoDQ)

Dataplex AutoDQ now supports advanced reusability and machine learning features. We recommend showcasing these capabilities in your demo:

### A. Rule Templates & Glossary-Based Association (Highlight Feature)
Instead of creating isolated rules for each table, build **Rule Templates** and associate them directly with your Business Glossary terms. Any column tagged with that term automatically inherits the rule!

* **Rule: Positive Stock Validation**
  * *Glossary Term*: **Current Stock Level**
  * *Dataplex Rule Type*: **Range**
  * *Min Value*: `0` (Leaves Max Value blank)
  * *Description*: Stock quantity cannot be negative.

* **Rule: Price Validation**
  * *Glossary Term*: **Standard Unit Price**
  * *Dataplex Rule Type*: **Range**
  * *Min Value*: `0.01`
  * *Description*: Unit price must be strictly greater than 0.

* **Rule: Valid Email Format**
  * *Glossary Term*: **Contact Email Address**
  * *Dataplex Rule Type*: **Regex**
  * *Regex Pattern*: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
  * *Description*: Email must follow standard format.

* **Rule: Valid Retail Branch**
  * *Glossary Term*: **Retail Branch Name**
  * *Dataplex Rule Type*: **Set**
  * *Allowed Values*: `London Flagship`, `Paris Central`, `Berlin Hub`, `Madrid Store`
  * *Description*: Branch name must belong to the active list of physical stores.

* **Rule: Unique Product Identifier**
  * *Glossary Term*: **Stock Keeping Unit (SKU)**
  * *Dataplex Rule Type*: **Uniqueness**
  * *Description*: Every SKU must be unique across the product catalog.

* **Rule: Mandatory Field**
  * *Glossary Term*: **Stock Keeping Unit (SKU)**
  * *Dataplex Rule Type*: **Non-null**
  * *Description*: A product must always have a registered SKU.

### B. AI-Generated Data Quality Rules
Leverage Dataplex's generative AI to automatically suggest rules based on table context. For instance, scanning the `customers` table might prompt the AI to suggest bounds for the `customer_segment` (e.g., standardizing tier strings).

---

## 4. Building the "Customer 360" Data Product

To support business questions like *"What is the average order value of high-loyalty customers in Europe?"*, package the underlying tables into a Dataplex Data Product:

1. **Create the Data Product**: Name it `Acme Customer 360 Insights`.
2. **Assign Ownership**: Assign the Marketing Analytics team as the primary stewards.
3. **Link Assets**: Attach the `customers`, `orders`, and `customer_360_view` BigQuery tables.
4. **Publish Glossary**: Ensure the `Customer Loyalty Index` and `Total Order Revenue` glossary terms are visible on the product page.
5. **Certify**: Apply the `Certified` aspect to signal to the AI Agent that this is the trusted, golden dataset for customer-related prompts.
