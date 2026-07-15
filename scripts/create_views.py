from google.cloud import bigquery

def create_views():
    client = bigquery.Client(project="kc-retail-demo")
    
    query_1 = """
    CREATE OR REPLACE VIEW `kc-retail-demo.raw_retail_data_euw1.customer_360_view` AS
    SELECT 
      c.customer_id,
      c.first_name,
      c.last_name,
      c.email,
      c.country,
      c.customer_segment,
      COUNT(o.order_id) as total_orders,
      SUM(o.total_amount) as lifetime_value
    FROM `kc-retail-demo.raw_retail_data_euw1.customers` c
    LEFT JOIN `kc-retail-demo.raw_retail_data_euw1.orders` o
      ON c.customer_id = o.customer_id
    GROUP BY 1,2,3,4,5,6
    """
    
    query_2 = """
    CREATE OR REPLACE VIEW `kc-retail-demo.raw_retail_data_euw1.unified_inventory_view` AS
    SELECT 
      i.inventory_id,
      i.product_id,
      p.product_name,
      i.store_id,
      i.stock_level,
      i.last_updated
    FROM `kc-retail-demo.raw_retail_data_euw1.inventory` i
    LEFT JOIN `kc-retail-demo.raw_retail_data_euw1.products` p
      ON i.product_id = p.product_id
    """
    
    print("Creating customer_360_view...")
    client.query(query_1).result()
    print("Creating unified_inventory_view...")
    client.query(query_2).result()
    print("Done!")

if __name__ == "__main__":
    create_views()
