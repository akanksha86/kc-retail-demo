#!/usr/bin/env python3
import os
import csv
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Ensure output directories exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UNSTRUCTURED_DIR = os.path.join(DATA_DIR, "unstructured")
MANUALS_DIR = os.path.join(UNSTRUCTURED_DIR, "manuals")
SOPS_DIR = os.path.join(UNSTRUCTURED_DIR, "sops")
CONTRACTS_DIR = os.path.join(UNSTRUCTURED_DIR, "contracts")

for d in [MANUALS_DIR, SOPS_DIR, CONTRACTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Styles
styles = getSampleStyleSheet()
title_style = styles['Heading1']
title_style.alignment = TA_CENTER
h2_style = styles['Heading2']
normal_style = styles['Normal']
normal_style.spaceAfter = 12

def create_pdf(filepath, title, paragraphs):
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    for p in paragraphs:
        if p.startswith("## "):
            story.append(Paragraph(p[3:], h2_style))
        else:
            story.append(Paragraph(p, normal_style))
            
    doc.build(story)
    print(f"Generated: {os.path.basename(filepath)}")

# Load products
products = []
products_csv = os.path.join(DATA_DIR, "products.csv")
if os.path.exists(products_csv):
    with open(products_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        products = list(reader)

# Load stores
stores = []
stores_csv = os.path.join(DATA_DIR, "stores.csv")
if os.path.exists(stores_csv):
    with open(stores_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        stores = list(reader)

random.seed(1234)

# 1. Generate Product Manuals
print("Generating Product Manuals...")
if products:
    # Pick 20 random active products
    active_products = [p for p in products if p['is_active'] == 'True']
    sample_products = random.sample(active_products, min(20, len(active_products)))
    
    for p in sample_products:
        pid = p['product_id']
        name = p['product_name']
        sku = p['sku']
        brand = p['brand']
        
        title = f"{name} - User Manual"
        paragraphs = [
            f"## Product Information",
            f"<b>Product Name:</b> {name}<br/><b>SKU:</b> {sku}<br/><b>Brand:</b> {brand}<br/><b>Category:</b> {p['category']}",
            f"<b>Description:</b> {p['description']}",
            "## Safety Instructions",
            "Please read all instructions before assembling or using this product. Keep away from direct sunlight and extreme temperatures. Do not use chemical solvents for cleaning.",
            "## Assembly Guide",
            "1. Unpack all components and lay them on a flat, soft surface.",
            "2. Verify all parts are present using the parts checklist.",
            "3. Follow the step-by-step diagrams provided in the accessory packet.",
            "4. Do not over-tighten screws to prevent damaging the material.",
            "## Maintenance & Care",
            "Wipe clean with a damp cloth. For tougher stains, use a mild soap solution. Inspect all connections periodically to ensure they remain tight and secure."
        ]
        
        filepath = os.path.join(MANUALS_DIR, f"{sku}_manual.pdf")
        create_pdf(filepath, title, paragraphs)

# 2. Generate Store SOPs
print("\nGenerating Store SOPs...")
if stores:
    # Pick 5 physical stores
    physical_stores = [s for s in stores if s['store_id'] != 'STR_000']
    sample_stores = random.sample(physical_stores, min(5, len(physical_stores)))
    
    sop_topics = [
        ("Opening and Closing Procedures", "Standard daily operations for unlocking doors, preparing registers, closing out tills, and activating alarm systems."),
        ("Inventory Count Protocol", "Guidelines for conducting monthly cycle counts, logging discrepancies, and reporting damaged goods in the inventory management system."),
        ("Customer Return Policy", "Steps for processing refunds, verifying original receipts, restocking undamaged items, and tagging defective merchandise for return to vendor (RTV).")
    ]
    
    for s in sample_stores:
        sid = s['store_id']
        sname = s['store_name']
        
        topic, desc = random.choice(sop_topics)
        
        title = f"{sname} - {topic}"
        paragraphs = [
            f"## Store Information",
            f"<b>Store ID:</b> {sid}<br/><b>Location:</b> {s['location']}, {s['region']}, {s['country']}",
            "## Standard Operating Procedure",
            desc,
            "## Compliance & Reporting",
            "Store managers are required to ensure all team members are trained on this SOP. Any deviations or incidents must be logged in the Store Operations Portal within 24 hours.",
            "Failure to comply with these procedures may result in disciplinary action. For support, contact the regional operations director."
        ]
        
        filename = f"{sid}_{topic.replace(' ', '_').lower()}.pdf"
        filepath = os.path.join(SOPS_DIR, filename)
        create_pdf(filepath, title, paragraphs)

# 3. Generate Vendor Contracts
print("\nGenerating Vendor Contracts...")
if products:
    brands = list(set([p['brand'] for p in products]))
    sample_brands = random.sample(brands, min(5, len(brands)))
    
    for brand in sample_brands:
        date = (datetime.now() - timedelta(days=random.randint(10, 500))).strftime("%B %d, %Y")
        
        title = f"Master Vendor Agreement: Acme Retail & {brand}"
        paragraphs = [
            f"## Agreement Overview",
            f"This Master Vendor Agreement (the 'Agreement') is entered into as of {date} by and between Acme Retail Inc. ('Retailer') and {brand} ('Vendor').",
            "## Terms of Supply",
            "Vendor agrees to supply Retailer with goods as specified in accepted Purchase Orders. All goods must meet the quality standards outlined in Exhibit A.",
            "## Pricing and Payment",
            "Retailer shall pay Vendor within Net 60 days of receiving a valid invoice. Prices are locked for the duration of this annual agreement unless renegotiated in writing by both parties.",
            "## Liability and Indemnification",
            "Vendor agrees to indemnify and hold Retailer harmless from any claims, damages, or liabilities arising out of product defects or intellectual property infringement related to the supplied goods.",
            "## Termination",
            "Either party may terminate this Agreement with 90 days written notice. Upon termination, Retailer reserves the right to sell through existing inventory or return it to Vendor at Vendor's expense."
        ]
        
        filename = f"Contract_{brand.replace(' ', '').replace('&', 'And')}.pdf"
        filepath = os.path.join(CONTRACTS_DIR, filename)
        create_pdf(filepath, title, paragraphs)

print("\nUnstructured PDF Generation Complete!")
