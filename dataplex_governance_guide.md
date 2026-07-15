# Dataplex Data Governance & Metadata Guide (Retail)

This guide outlines the data governance structure, manual metadata mappings, recommended Data Quality rules, and Data Product topologies for the Acme Retail environment.

## 1. Metadata Mapping (Aspects & Glossary)

*Attach Aspects via Knowledge Catalog > Entries > Attach Aspect.*
*Attach Glossary Terms via Knowledge Catalog > Entries > Schema Tab > Attach Glossary Term.*

### Core Tables
| BigQuery Table | Custom Aspect Type to Attach | Data to enter in UI | Glossary Terms (Column Level) |
| :--- | :--- | :--- | :--- |
| **`customers`** | `data-owner` | `customer-success@acme.com` | `loyalty_score` -> **Customer Loyalty Index** <br> `email` -> **Contact Email Address** |
| | `contains-pii` | `True` | |
| **`orders`** | `data-owner` | `sales-ops@acme.com` | `total_amount` -> **Total Order Revenue** |
| | `contains-pii` | `True` | |
| **`products`** | `data-owner` | `merchandising@acme.com` | `unit_price` -> **Standard Unit Price** <br> `sku` -> **Stock Keeping Unit (SKU)** |
| | `contains-pii` | `False` | |
| **`inventory`** | `data-owner` | `supply-chain@acme.com` | `stock_quantity` -> **Current Stock Level** <br> `last_updated` -> **Inventory Snapshot Time** |
| | `contains-pii` | `False` | |
| **`stores`** | `data-owner` | `retail-ops@acme.com` | `store_name` -> **Retail Branch Name** |
| | `contains-pii` | `False` | |

### Aggregated / Unified Views
| BigQuery Table | Custom Aspect Type to Attach | Data to enter in UI | Glossary Terms (Column Level) |
| :--- | :--- | :--- | :--- |
| **`customer_360_view`** | `data-owner` | `marketing-analytics@acme.com` | Inherits from underlying columns |
| | `contains-pii` | `True` | |
| **`real_time_inventory_view`** | `data-owner` | `supply-chain@acme.com` | Inherits from underlying columns |
| | `contains-pii` | `False` | |

---

## 2. Architecture Recommendation: Real-Time POS Data Integration

**How should streaming Point-of-Sale (POS) transactions be integrated with historical orders and inventory?**
* **Via Materialized Views.** The main `orders` and `order_items` tables often serve as large historical repositories. Injecting high-velocity streaming POS data directly into static batch tables can cause performance and cost issues. 
* **Best Practice**: Create a **BigQuery View** (or Materialized View) that performs a `UNION ALL` between the historical `orders` table and a real-time `streaming_pos_transactions` table. This ensures the Conversational Agent can instantly query the latest sales and inventory deductions alongside historical trends without degrading database performance.

---

## 3. Recommended Data Quality Rules (AutoDQ)

Dataplex AutoDQ now supports advanced reusability and machine learning features. We recommend showcasing these capabilities in your demo:

### A. Rule Templates & Glossary-Based Association (Highlight Feature)
Instead of creating isolated rules for each table, build **Rule Templates** and associate them directly with your Business Glossary terms. Any column tagged with that term automatically inherits the rule!

* **Rule: Positive Stock Validation**
  * *Glossary Term*: **Current Stock Level**
  * *Description*: Stock quantity cannot be negative.
  * *Template Expression*: `${data()} < 0` (Identifies invalid rows)

* **Rule: Price Validation**
  * *Glossary Term*: **Standard Unit Price**
  * *Description*: Unit price must be strictly greater than 0.
  * *Template Expression*: `${data()} <= 0` (Identifies invalid rows)

* **Rule: Valid Email Format**
  * *Glossary Term*: **Contact Email Address**
  * *Description*: Email must follow standard format.
  * *Template Expression*: `NOT REGEXP_CONTAINS(${data()}, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')`

### B. AI-Generated Data Quality Rules
Leverage Dataplex's generative AI to automatically suggest rules based on table context. For instance, scanning the `customers` table might prompt the AI to suggest bounds for the `loyalty_score` (e.g., between 0 and 1000).

---

## 4. Building the "Customer 360" Data Product

To support business questions like *"What is the average order value of high-loyalty customers in Europe?"*, package the underlying tables into a Dataplex Data Product:

1. **Create the Data Product**: Name it `Acme Customer 360 Insights`.
2. **Assign Ownership**: Assign the Marketing Analytics team as the primary stewards.
3. **Link Assets**: Attach the `customers`, `orders`, and `customer_360_view` BigQuery tables.
4. **Publish Glossary**: Ensure the `Customer Loyalty Index` and `Total Order Revenue` glossary terms are visible on the product page.
5. **Certify**: Apply the `Certified` aspect to signal to the AI Agent that this is the trusted, golden dataset for customer-related prompts.
