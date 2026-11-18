import os 
import sqlite3
import pandas as pd
from sqlalchemy import create_engine 

# Extract Transform Load data
def run_etl_pipeline(raw_data_dir : str = "data_raw" , db_url : str ="sqlite:///ecommerce_analytics.db"): 
    print("=== [PHASE 1] Starting Ingestion & Cleaning Pipeline ===")
    engine =  create_engine(db_url)

    # Reading raw CSV files & Genrating data if not available
    customer_path = os.path.join(raw_data_dir,"customers.csv")
    products_path = os.path.join(raw_data_dir,"products.csv")
    orders_path = os.path.join(raw_data_dir,"orders.csv")
    items_path = os.path.join(raw_data_dir,"order_items.csv")

    if not all(os.path.exists(p) for p in [customer_path,products_path,orders_path,items_path]) :
        from generate_data import generate_synthetic_data
        print("Raw data files missing. Generating synthetic dataset...")
        generate_synthetic_data(output_dir=raw_data_dir)
    df_cust = pd.read_csv(customer_path)
    df_prod = pd.read_csv(products_path)
    df_ord = pd.read_csv(orders_path)
    df_items = pd.read_csv(items_path)

    print(f"Loaded raw records -> Customers :{len(df_cust)},Products : {len(df_prod)}, Orders: {len(df_ord)},Order Items : {len(df_items)}")

    # Data cleaning & normalization
    
    df_items.drop_duplicates(subset = ["order_item_id"] ,keep="first",inplace=True)
    df_ord.drop_duplicates(subset=["order_id"],keep="first",inplace=True)

    df_ord.dropna(subset=["order_timestamp"],inplace=True)

    df_ord["order_timestamp"] = pd.to_datetime(df_ord["order_timestamp"])
    df_cust["created_at"] = pd.to_datetime(df_cust["created_at"])

    df_items = df_items[(df_items["item_price"]>0)&(df_items["quantity"] > 0)].copy()

    # loading data into database
    with engine.begin() as conn :
        df_cust.to_sql("customers" , conn , if_exists="replace",index=False)
        df_prod.to_sql("products" , conn , if_exists="replace",index=False)
        df_ord.to_sql("orders" , conn , if_exists="replace",index=False)
        df_items.to_sql("order_items" , conn ,if_exists="replace",index=False)

    print("=== Pipeline Complete: Database Populating Completed Successfully ! ===")

if __name__ == "__main__" :
    run_etl_pipeline() 