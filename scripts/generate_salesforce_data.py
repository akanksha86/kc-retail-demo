import csv
import random
from datetime import datetime, timedelta
import os

# Set seed for reproducibility
random.seed(42)

print("Generating synthetic Salesforce Service Cloud data...")

# Load existing customers and products
customer_ids = []
with open('data/customers.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        customer_ids.append(row['customer_id'])

product_ids = []
with open('data/products.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        product_ids.append(row['product_id'])

num_cases = 5000
case_ids = [f"CAS-{str(i).zfill(6)}" for i in range(1, num_cases + 1)]

# Generate dates within the last year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
created_dates = [start_date + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23)) for _ in range(num_cases)]
created_dates.sort() # Sort chronologically

statuses = ['New', 'In Progress', 'Escalated', 'Closed']
priorities = ['Low', 'Medium', 'High', 'Critical']
subjects = [
    "Product arrived damaged", 
    "Where is my order?", 
    "Need help with assembly", 
    "Warranty claim inquiry", 
    "Missing parts in box", 
    "Return request", 
    "Defective item",
    "Billing question"
]

def get_weighted_random(choices, weights):
    return random.choices(choices, weights=weights, k=1)[0]

data = []
for i in range(num_cases):
    status = get_weighted_random(statuses, [0.1, 0.2, 0.05, 0.65])
    priority = get_weighted_random(priorities, [0.4, 0.4, 0.15, 0.05])
    
    res_time = ""
    if status == 'Closed':
        res_time = str(round(random.uniform(1, 168), 1))
        
    data.append({
        'case_id': case_ids[i],
        'customer_id': random.choice(customer_ids),
        'product_id': random.choice(product_ids),
        'status': status,
        'priority': priority,
        'subject': random.choice(subjects),
        'created_date': created_dates[i].strftime('%Y-%m-%d %H:%M:%S'),
        'resolution_time_hours': res_time
    })

# Save to CSV
os.makedirs('data', exist_ok=True)
with open('data/salesforce_service_cases.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['case_id', 'customer_id', 'product_id', 'status', 'priority', 'subject', 'created_date', 'resolution_time_hours'])
    writer.writeheader()
    writer.writerows(data)

print(f"Successfully generated {num_cases} Salesforce support cases.")
print("Saved to data/salesforce_service_cases.csv")
