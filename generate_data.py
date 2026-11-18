import os 
import random 
import uuid
from datetime import datetime , timedelta
import numpy as np 
import pandas as pd
from faker import Faker


fake = Faker()
Faker.seed(36)
np.random.seed(36)
random.seed(36)

def generate_synthetic_data(num_customers=1000,num_orders=10000,output_dir = "data_raw") :
    os.makedirs(output_dir,exist_ok=True)

    # generating customer details dataframe
    channels = ["Paid Search" , "Organic" , "Social Media" , "Referral" , "Direct"]
    customers = []
    start_date = datetime(2024,1,1)

    for _ in range(num_customers) :
        created = start_date +timedelta(days=random.randint(0,365))
        customers.append({
            "customer_id" : str(uuid.uuid4()),
            "first_name" : fake.first_name(),
            "last_name" : fake.last_name(),
            "email" : fake.email(),
            "acquisition_channel" : random.choice(channels),
            "created_at" : created
         })

    
    df_customers = pd.DataFrame(customers)

    # generating products details dataframe
    categories = {
        "Electronics" :[
            ('Headphones' , 99.99 , 45.00),
            ("Smartwatch" ,199.99 , 90.00),
            ("Laptop" , 899.99 ,500.00),
            ("Wireless Mouse" , 29.99 ,12.00),
            ("USB-C Cable" , 15.00 , 4.00)
        ],
        "Apparel" : [
            ("T-Shirt" , 25.00 ,8.00),
            ("Jeans" , 60.00 , 20.00),
            ("Jacket" , 120.00 ,45.00),
            ("Sneakers",85.00,35.00),
            ("Socks Pack" , 12.00 ,3.00)
        ],
        "Home Goods" : [
            ("Coffee Maker" , 80.00 , 30.00),
            ("Blender" , 45.00 , 15.00),
            ("Desk Lamp" , 30.00 ,10.00),
            ("Air Purifier" , 150.00 ,70.00),
            ("Throw Blanket" , 35.00 , 12.00)
        ]
    }

    products = []

    for cat , items in categories.items() :
        for p_name ,price , cost in items :
            products.append({
                "product_id" : str(uuid.uuid4()),
                "product_name" : p_name ,
                "category" : cat ,
                "unit_price" : price ,
                "cost_price" : cost
            })
    df_products = pd.DataFrame(products)

    # Generating Orders & Order Items dataframes
    orders = []
    order_items = []
    statuses = ["Completed" , "Completed" ,"Completed" , "Completed" , "Refunded" , "Cancelled"]

    for _ in range(num_orders) :
        cust = df_customers.sample(1).iloc[0]
        order_date = cust["created_at"] + timedelta(days=random.randint(0,180),minutes=random.randint(0,1440)) 
        order_id = str(uuid.uuid4())
        status = random.choice(statuses)
        # adding anomaly missing timestamp
        if random.random() <0.01 :
            order_date = np.nan

        orders.append({
            "order_id" : order_id ,
            "customer_id" : cust["customer_id"],
            "order_status" : status ,
            "order_timestamp" : order_date ,
            "shipping_cost" : round(random.uniform(0.0,15.0),2)

        })

        # 1 to 4 items can be in one order
        num_items = random.randint(1,4) 
        selected_prods = df_products.sample(num_items)

        for _, prod in selected_prods.iterrows() :
            qty = random.randint(1,3)
            item_price = prod["unit_price"]

            if random.random() < 0.005 :
                item_price = -1.0 * item_price

            order_items.append({
                "order_item_id" : str(uuid.uuid4()),
                "order_id" : order_id ,
                "product_id" : prod["product_id"],
                "quantity" : qty ,
                "item_price" : item_price
            })

    df_orders = pd.DataFrame(orders)
    df_order_items = pd.DataFrame(order_items)

    # adding anomaly synthetic duplicate rows
    df_order_items = pd.concat([df_order_items ,df_order_items.head(50)],ignore_index=True)

    df_customers.to_csv(os.path.join(output_dir , "customers.csv"),index=False)
    df_products.to_csv(os.path.join(output_dir,"products.csv"),index=False)
    df_orders.to_csv(os.path.join(output_dir,"orders.csv"),index=False)
    df_order_items.to_csv(os.path.join(output_dir,"order_items.csv"),index= False)


    print(f"Dataset generated cleanly in directory : '{output_dir}'")

if __name__ == "__main__" :
    generate_synthetic_data()