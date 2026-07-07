#!/usr/bin/env python3
import csv
import os
import random
import datetime
import hashlib
import string

# Set seed for reproducibility
random.seed(42)

# Directory for output files
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Master list of names for synthetic generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
    "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
    "Donald", "Ashley", "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna",
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Timothy", "Deborah",
    "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon", "Jeffrey", "Laura", "Gary", "Cynthia",
    "Ryan", "Kathleen", "Nicholas", "Amy", "Shirley", "Eric", "Angela", "Stephen", "Helen", "Jonathan",
    "Anna", "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma", "Benjamin",
    "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Alexander", "Debra", "Frank", "Rachel",
    "Patrick", "Carolyn", "Raymond", "Janet", "Jack", "Maria", "Dennis", "Heather", "Jerry", "Catherine",
    "Tyler", "Aaron", "Henry", "Jose", "Douglas", "Peter", "Walter", "Arthur", "Harold", "Jose"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
    "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
    "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez",
    "Porter", "Hunter", "Webb", "Mason", "Sutton", "Shaw", "Jordan", "Palmer", "Robertson", "Gibson"
]

STREETS = [
    "Maple St", "Oak Ave", "Pine Rd", "Broadway", "Sunset Blvd", "Main St", "Washington St", "Park Ln",
    "Elm St", "Cedar Ave", "View Rd", "Forest Ave", "Lake Dr", "River Rd", "Hillcrest Dr", "Ridge Rd",
    "Meadow Ln", "Highland Ave", "Spring St", "Willow St", "Church St", "Lincoln St", "Union St", "Market St",
    "1st Ave", "2nd St", "3rd St", "4th Ave", "Peachtree St", "Sherman Way", "Grand Ave", "Victoria Rd",
    "King St", "Queen St", "Baker St", "High St", "Mill Rd", "Station Rd", "Green Ln", "London Rd"
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "acme-corp.com", "proto-mail.com"]

# Geographical hierarchy matching stores and customer distribution
GEOGRAPHY = [
    {"code": "US", "country": "United States", "city": "New York", "state": "NY", "zip_prefix": "100", "area_code": "212"},
    {"code": "US", "country": "United States", "city": "Los Angeles", "state": "CA", "zip_prefix": "900", "area_code": "310"},
    {"code": "US", "country": "United States", "city": "Chicago", "state": "IL", "zip_prefix": "606", "area_code": "312"},
    {"code": "US", "country": "United States", "city": "Houston", "state": "TX", "zip_prefix": "770", "area_code": "713"},
    {"code": "US", "country": "United States", "city": "Miami", "state": "FL", "zip_prefix": "331", "area_code": "305"},
    {"code": "US", "country": "United States", "city": "Seattle", "state": "WA", "zip_prefix": "981", "area_code": "206"},
    {"code": "US", "country": "United States", "city": "Boston", "state": "MA", "zip_prefix": "021", "area_code": "617"},
    {"code": "UK", "country": "United Kingdom", "city": "London", "state": "England", "zip_prefix": "SW1A", "area_code": "020"},
    {"code": "UK", "country": "United Kingdom", "city": "Manchester", "state": "England", "zip_prefix": "M1", "area_code": "0161"},
    {"code": "UK", "country": "United Kingdom", "city": "Edinburgh", "state": "Scotland", "zip_prefix": "EH1", "area_code": "0131"},
    {"code": "CA", "country": "Canada", "city": "Toronto", "state": "ON", "zip_prefix": "M5V", "area_code": "416"},
    {"code": "CA", "country": "Canada", "city": "Vancouver", "state": "BC", "zip_prefix": "V6B", "area_code": "604"},
    {"code": "CA", "country": "Canada", "city": "Montreal", "state": "QC", "zip_prefix": "H3B", "area_code": "514"},
    {"code": "DE", "country": "Germany", "city": "Berlin", "state": "Berlin", "zip_prefix": "10115", "area_code": "030"},
    {"code": "DE", "country": "Germany", "city": "Munich", "state": "Bavaria", "zip_prefix": "80331", "area_code": "089"},
    {"code": "DE", "country": "Germany", "city": "Hamburg", "state": "Hamburg", "zip_prefix": "20095", "area_code": "040"},
    {"code": "FR", "country": "France", "city": "Paris", "state": "Île-de-France", "zip_prefix": "75001", "area_code": "01"},
    {"code": "FR", "country": "France", "city": "Lyon", "state": "Auvergne-Rhône-Alpes", "zip_prefix": "69001", "area_code": "04"},
    {"code": "JP", "country": "Japan", "city": "Tokyo", "state": "Tokyo", "zip_prefix": "100-0001", "area_code": "03"},
    {"code": "JP", "country": "Japan", "city": "Osaka", "state": "Osaka", "zip_prefix": "530-0001", "area_code": "06"},
    {"code": "AU", "country": "Australia", "city": "Sydney", "state": "NSW", "zip_prefix": "2000", "area_code": "02"},
    {"code": "AU", "country": "Australia", "city": "Melbourne", "state": "VIC", "zip_prefix": "3000", "area_code": "03"}
]

# Product definition models (brand, category, patterns)
PRODUCT_CATEGORIES = {
    "Furniture": {
        "items": [
            ("Sofa", 450, 1800), ("Dining Table", 300, 1200), ("Dining Chair", 60, 250),
            ("Coffee Table", 100, 450), ("Bookshelf", 80, 400), ("Desk", 120, 600),
            ("Bed Frame", 250, 1000), ("Nightstand", 50, 200), ("Wardrobe", 350, 1500),
            ("Sideboard", 200, 800), ("Armchair", 150, 600)
        ],
        "brands": ["Acme Living", "Nordic Craft", "SleekSteel", "Heritage Oak"]
    },
    "Lighting": {
        "items": [
            ("Pendant Light", 40, 300), ("Table Lamp", 20, 150), ("Floor Lamp", 50, 250),
            ("Wall Sconce", 25, 120), ("Chandelier", 150, 1000), ("Desk Lamp", 15, 80)
        ],
        "brands": ["Lumina Design", "GlowStudio", "Edison & Co."]
    },
    "Decor": {
        "items": [
            ("Area Rug", 80, 600), ("Throw Pillow", 15, 50), ("Wall Mirror", 30, 200),
            ("Ceramic Vase", 10, 80), ("Canvas Wall Art", 25, 250), ("Scented Candle", 8, 30),
            ("Table Runner", 12, 45), ("Wall Clock", 15, 90)
        ],
        "brands": ["Terra Clay", "Elegance Decor", "Artisan Weave", "Minimalist Home"]
    },
    "Bed & Bath": {
        "items": [
            ("Organic Sheet Set", 40, 150), ("Duvet Cover Set", 50, 200), ("Pillow Set", 20, 80),
            ("Bath Towel Set", 18, 70), ("Shower Curtain", 10, 40), ("Bath Mat", 8, 30)
        ],
        "brands": ["Loom & Thread", "CozyNest", "Cloud Soft"]
    },
    "Kitchen & Dining": {
        "items": [
            ("Dinnerware Set", 50, 250), ("Cookware Set", 80, 400), ("Cutlery Set", 30, 150),
            ("Wine Glass Set", 15, 80), ("Ceramic Serving Bowl", 12, 50), ("Wood Cutting Board", 15, 60)
        ],
        "brands": ["Acme Chef", "Terra Cotta", "Iron & Clay"]
    },
    "Storage & Organization": {
        "items": [
            ("Wire Shelving", 30, 120), ("Woven Storage Basket", 10, 45), ("Fabric Closet Organizer", 12, 40),
            ("Shoe Rack", 15, 60), ("Stackable Plastic Bin Set", 12, 50)
        ],
        "brands": ["SpaceSavers", "Acme Tidy", "Box & Bin"]
    }
}

STYLES = ["Modernist", "Nordic", "Rustic", "Artisan", "Minimalist", "Industrial", "Bohemian", "Classic", "Contemporary", "Vintage"]
MATERIALS = ["Walnut", "Oak", "Teak", "Steel", "Marble", "Linen", "Ceramic", "Glass", "Bamboo", "Brass", "Wool"]

# Scale configurations
SCALE = {
    "stores": 21,  # 20 physical + 1 online
    "products": 1500,
    "customers": 20000,
    "orders": 100000,
}

print(f"Starting data generation for Acme Retail in directory: {OUTPUT_DIR}")

# ----------------- 1. GENERATE STORES -----------------
print("Generating Stores...")
stores = []
# Add Online Store
stores.append({
    "store_id": "STR_000",
    "store_name": "Acme Retail Online",
    "location": "Global Fulfillment Warehouse",
    "region": "Online",
    "country": "Online"
})

for i, geo in enumerate(GEOGRAPHY, 1):
    sid = f"STR_{i:03d}"
    street_num = random.randint(100, 2500)
    street_name = random.choice(STREETS)
    stores.append({
        "store_id": sid,
        "store_name": f"Acme Retail {geo['city']}",
        "location": f"{street_num} {street_name}",
        "region": geo["state"],
        "country": geo["country"]
    })

with open(os.path.join(OUTPUT_DIR, "stores.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=stores[0].keys())
    writer.writeheader()
    writer.writerows(stores)


# ----------------- 2. GENERATE PRODUCTS -----------------
print("Generating Products...")
products = []
used_skus = set()

# Seed categories list to cycle through
categories_keys = list(PRODUCT_CATEGORIES.keys())

for idx in range(1, SCALE["products"] + 1):
    pid = f"PRD_{idx:04d}"
    
    # Pick category
    cat = categories_keys[idx % len(categories_keys)]
    cat_info = PRODUCT_CATEGORIES[cat]
    
    # Pick a random item type template
    item_type, min_p, max_p = random.choice(cat_info["items"])
    style = random.choice(STYLES)
    material = random.choice(MATERIALS)
    brand = random.choice(cat_info["brands"])
    
    product_name = f"{style} {material} {item_type}"
    description = f"A premium quality {style.lower()} {item_type.lower()} crafted from durable {material.lower()}. Designed by {brand}."
    
    # Unit price rounded to 2 decimal places
    unit_price = round(random.uniform(min_p, max_p), 2)
    
    # Generate unique SKU
    sku_base = f"{brand[:3].upper()}-{cat[:3].upper()}-{item_type[:3].upper()}"
    sku_rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    sku = f"{sku_base}-{sku_rand}"
    while sku in used_skus:
        sku_rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        sku = f"{sku_base}-{sku_rand}"
    used_skus.add(sku)
    
    # 95% of products are active
    is_active = "True" if random.random() < 0.95 else "False"
    
    products.append({
        "product_id": pid,
        "product_name": product_name,
        "description": description,
        "category": cat,
        "brand": brand,
        "unit_price": unit_price,
        "sku": sku,
        "is_active": is_active
    })

with open(os.path.join(OUTPUT_DIR, "products.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)


# ----------------- 3. GENERATE CUSTOMERS -----------------
print("Generating Customers...")
customers = []
customer_ids = []
start_date = datetime.date(2022, 1, 1)
end_date = datetime.date(2026, 6, 30)
days_range = (end_date - start_date).days

for idx in range(1, SCALE["customers"] + 1):
    cid = f"CUST_{idx:05d}"
    customer_ids.append(cid)
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Deterministic but realistic email
    email = f"{first_name.lower()}.{last_name.lower()}.{idx:02d}@{random.choice(DOMAINS)}"
    
    # Choose geography for customer
    geo = random.choice(GEOGRAPHY)
    
    # Format phone number
    phone_serial = random.randint(100, 9999)
    if geo["code"] == "US":
        phone = f"+1-{geo['area_code']}-555-{phone_serial:04d}"
        zip_code = f"{geo['zip_prefix']}{random.randint(10, 99):02d}"
    elif geo["code"] == "UK":
        phone = f"+44-{geo['area_code']}-7700-{phone_serial:03d}"
        zip_code = f"{geo['zip_prefix']} {random.randint(1, 9)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"
    elif geo["code"] == "DE":
        phone = f"+49-{geo['area_code']}-{random.randint(100,999)}-{phone_serial:04d}"
        zip_code = f"{geo['zip_prefix']}"
    elif geo["code"] == "JP":
        phone = f"+81-{geo['area_code']}-{random.randint(100,999)}-{phone_serial:04d}"
        zip_code = f"{geo['zip_prefix']}"
    else:
        phone = f"+{geo['area_code']}-{random.randint(100,999)}-{phone_serial:04d}"
        zip_code = f"{geo['zip_prefix']}{random.randint(100,999)}"
        
    street_num = random.randint(10, 1500)
    address = f"{street_num} {random.choice(STREETS)}"
    
    # Registration date
    reg_days = random.randint(0, days_range)
    reg_date = start_date + datetime.timedelta(days=reg_days)
    
    # Segments
    segment_roll = random.random()
    if segment_roll < 0.10:
        segment = "VIP"
    elif segment_roll < 0.70:
        segment = "Regular"
    else:
        segment = "New"
        
    customers.append({
        "customer_id": cid,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "address": address,
        "city": geo["city"],
        "state": geo["state"],
        "zip_code": zip_code,
        "country": geo["country"],
        "registration_date": reg_date.isoformat(),
        "customer_segment": segment
    })

with open(os.path.join(OUTPUT_DIR, "customers.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
    writer.writeheader()
    writer.writerows(customers)


# ----------------- 4. GENERATE ORDERS & ORDER ITEMS -----------------
print("Generating Orders and Order Items...")
orders = []
order_items = []
order_item_idx = 1

order_statuses = ["Delivered", "Delivered", "Delivered", "Delivered", "Shipped", "Pending", "Cancelled"]

# Load customer dates into dictionary for quick access
cust_reg_dates = {c["customer_id"]: datetime.date.fromisoformat(c["registration_date"]) for c in customers}
# Load product prices for reference
prod_prices = {p["product_id"]: p["unit_price"] for p in products}
product_ids_list = list(prod_prices.keys())
store_ids_list = [s["store_id"] for s in stores]

# We want 100,000 orders
for o_idx in range(1, SCALE["orders"] + 1):
    oid = f"ORD_{o_idx:06d}"
    
    # Pick a random customer
    cid = random.choice(customer_ids)
    reg_date = cust_reg_dates[cid]
    
    # Pick an order date that is on or after the customer registration date
    max_days = (end_date - reg_date).days
    if max_days <= 0:
        order_date = reg_date
    else:
        order_date = reg_date + datetime.timedelta(days=random.randint(0, max_days))
        
    # Order channel/Store: 30% online, 70% physical stores
    if random.random() < 0.30:
        sid = "STR_000"  # Online Store
    else:
        sid = random.choice(store_ids_list[1:])  # Physical Store
        
    # Status
    status = random.choice(order_statuses)
    
    # Shipping info (default to customer's profile info)
    cust_info = customers[int(cid.split("_")[1]) - 1]
    
    # Create order line items (1 to 6 items per order)
    num_items = random.randint(1, 6)
    chosen_products = random.sample(product_ids_list, num_items)
    
    order_total = 0.0
    
    for pid in chosen_products:
        item_id = f"ORI_{order_item_idx:07d}"
        qty = random.choices([1, 2, 3, 4, 5], weights=[60, 25, 10, 3, 2])[0]
        price = prod_prices[pid]
        
        order_items.append({
            "order_item_id": item_id,
            "order_id": oid,
            "product_id": pid,
            "quantity": qty,
            "price_per_unit": price
        })
        
        order_total += qty * price
        order_item_idx += 1

    orders.append({
        "order_id": oid,
        "customer_id": cid,
        "store_id": sid,
        "order_date": order_date.isoformat(),
        "order_status": status,
        "shipping_address": cust_info["address"],
        "shipping_city": cust_info["city"],
        "shipping_state": cust_info["state"],
        "shipping_zip": cust_info["zip_code"],
        "shipping_country": cust_info["country"],
        "total_amount": round(order_total, 2)
    })
    
    if o_idx % 20000 == 0:
        print(f"  Generated {o_idx} orders...")

print("Saving Orders...")
with open(os.path.join(OUTPUT_DIR, "orders.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows(orders)

print("Saving Order Items...")
with open(os.path.join(OUTPUT_DIR, "order_items.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
    writer.writeheader()
    writer.writerows(order_items)


# ----------------- 5. GENERATE INVENTORY -----------------
print("Generating Inventory records...")
inventory = []
inv_idx = 1

# Generate stock level for all active products in all stores
active_products = [p["product_id"] for p in products if p["is_active"] == "True"]

# Reference date for inventory update
inv_base_time = datetime.datetime.now() - datetime.timedelta(hours=6)

for store in stores:
    sid = store["store_id"]
    for pid in active_products:
        inv_id = f"INV_{inv_idx:06d}"
        
        # Online store/fulfillment center has higher stock levels
        if sid == "STR_000":
            stock = random.randint(100, 1000)
        else:
            stock = random.choices(
                [random.randint(5, 50), random.randint(51, 150), 0],
                weights=[60, 35, 5]  # 5% chance of out-of-stock
            )[0]
            
        # Last updated timestamp (within last 12 hours)
        last_up = inv_base_time + datetime.timedelta(minutes=random.randint(0, 360))
        
        inventory.append({
            "inventory_id": inv_id,
            "store_id": sid,
            "product_id": pid,
            "stock_level": stock,
            "last_updated": last_up.strftime("%Y-%m-%d %H:%M:%S")
        })
        inv_idx += 1

print("Saving Inventory...")
with open(os.path.join(OUTPUT_DIR, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=inventory[0].keys())
    writer.writeheader()
    writer.writerows(inventory)

print("Data generation complete!")
print(f"Files written to {OUTPUT_DIR}:")
print(f" - stores.csv ({len(stores)} rows)")
print(f" - products.csv ({len(products)} rows)")
print(f" - customers.csv ({len(customers)} rows)")
print(f" - orders.csv ({len(orders)} rows)")
print(f" - order_items.csv ({len(order_items)} rows)")
print(f" - inventory.csv ({len(inventory)} rows)")
