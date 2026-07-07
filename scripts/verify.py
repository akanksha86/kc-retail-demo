import csv
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")

def load_keys(file_path, key_column):
    keys = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys.add(row[key_column])
    return keys

print("Verifying referential integrity...")

# Load PKs
store_ids = load_keys(os.path.join(data_dir, "stores.csv"), "store_id")
product_ids = load_keys(os.path.join(data_dir, "products.csv"), "product_id")
customer_ids = load_keys(os.path.join(data_dir, "customers.csv"), "customer_id")
order_ids = load_keys(os.path.join(data_dir, "orders.csv"), "order_id")

print(f"Loaded {len(store_ids)} stores.")
print(f"Loaded {len(product_ids)} products.")
print(f"Loaded {len(customer_ids)} customers.")
print(f"Loaded {len(order_ids)} orders.")

# Verify Orders
orders_errors = 0
with open(os.path.join(data_dir, "orders.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["customer_id"] not in customer_ids:
            print(f"Error: customer_id {row['customer_id']} in order {row['order_id']} does not exist in customers.")
            orders_errors += 1
        if row["store_id"] not in store_ids:
            print(f"Error: store_id {row['store_id']} in order {row['order_id']} does not exist in stores.")
            orders_errors += 1

# Verify Order Items
item_errors = 0
order_items_count = 0
with open(os.path.join(data_dir, "order_items.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        order_items_count += 1
        if row["order_id"] not in order_ids:
            print(f"Error: order_id {row['order_id']} in order_item {row['order_item_id']} does not exist in orders.")
            item_errors += 1
        if row["product_id"] not in product_ids:
            print(f"Error: product_id {row['product_id']} in order_item {row['order_item_id']} does not exist in products.")
            item_errors += 1

# Verify Inventory
inventory_errors = 0
inventory_count = 0
with open(os.path.join(data_dir, "inventory.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        inventory_count += 1
        if row["store_id"] not in store_ids:
            print(f"Error: store_id {row['store_id']} in inventory {row['inventory_id']} does not exist in stores.")
            inventory_errors += 1
        if row["product_id"] not in product_ids:
            print(f"Error: product_id {row['product_id']} in inventory {row['inventory_id']} does not exist in products.")
            inventory_errors += 1

print("\n--- Integrity Verification Summary ---")
print(f"Orders verified: {len(order_ids)} | Errors: {orders_errors}")
print(f"Order Items verified: {order_items_count} | Errors: {item_errors}")
print(f"Inventory records verified: {inventory_count} | Errors: {inventory_errors}")

if orders_errors == 0 and item_errors == 0 and inventory_errors == 0:
    print("Verification SUCCESS: All references are valid and consistent!")
else:
    print("Verification FAILED: Errors found.")
