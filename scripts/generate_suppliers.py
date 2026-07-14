import csv
import random
import os

print("Generating synthetic Suppliers (Legacy Database) data...")
suppliers = []
cities = ["New York", "London", "Tokyo", "Berlin", "Paris", "Sydney", "Mumbai", "Sao Paulo"]

# deterministic
random.seed(42)

for i in range(1, 101):
    suppliers.append({
        'supplier_id': f"SUP-{str(i).zfill(3)}",
        'supplier_name': f"Supplier {i} Corp",
        'contact_email': f"contact@supplier{i}.com",
        'city': random.choice(cities),
        'rating': round(random.uniform(2.5, 5.0), 1)
    })

os.makedirs('data', exist_ok=True)
with open('data/suppliers.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['supplier_id', 'supplier_name', 'contact_email', 'city', 'rating'])
    writer.writeheader()
    writer.writerows(suppliers)
print("Saved 100 suppliers to data/suppliers.csv")
