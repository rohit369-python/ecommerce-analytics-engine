import datetime as dt
import numpy as np 
import pandas as pd
from sqlalchemy import create_engine 


# Creates and returns a SQLAlchemy database connection engine using the provided database URL string.
def get_db_connection(db_url = "sqlite:///ecommerce_analytics.db"):
    return create_engine(db_url)

# key performance indicator like total revenue , total order , total customer , average order value
def compute_executive_kpis(engine) :
    
    query = """
    SELECT 
        o.order_id,
        o.customer_id,
        o.order_status ,
        o.order_timestamp,
        oi.quantity * oi.item_price AS line_total,
        p.category
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'Completed'
    """
    
    df = pd.read_sql(query , engine)

    total_revenue = df["line_total"].sum()
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_id"].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0

    return {
        "Total Revenue" : round(total_revenue,2),
        "Total Orders" : total_orders ,
        "Unique Buyers" : total_customers ,
        "Average Order Value (AOV)" : round(aov , 2)
    }

# computing recency , frequency , monetary value and segmenting customer based on these parameters
def compute_rfm_segmentation(engine) :
    query = """
    SELECT 
        o.customer_id ,
        o.order_id,
        o.order_timestamp,
        (oi.quantity * oi.item_price) AS line_total
    FROM orders o 
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    
    """
    df = pd.read_sql(query , engine)

    df["order_timestamp"] = pd.to_datetime(df["order_timestamp"])

    order_spend = df.groupby(["customer_id","order_id","order_timestamp"])["line_total"].sum().reset_index()
    max_date = order_spend["order_timestamp"].max() + dt.timedelta(days=1)

    rfm = order_spend.groupby("customer_id").agg(
        Recency = ("order_timestamp" , lambda x :(max_date - x.max()).days),
        Frequency = ("order_id" , "nunique"),
        Monetary = ("line_total" , "sum")
    
    ).reset_index()




    rfm["R_Score"] = pd.qcut(rfm["Recency"],q=4,labels=[4,3,2,1],duplicates="drop").astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"),q=4,labels=[1,2,3,4],duplicates="drop").astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"],q=4,labels=[1,2,3,4],duplicates="drop").astype(int)

    

    def assign_segment(r) :

        if r["R_Score"] >= 3 and r["F_Score"] >= 3 and r["M_Score"] >= 3 :
            return "Champions" # best, most active, and highest-spending customers

        elif r["R_Score"] >= 3 and r["F_Score"] >=2 :
            return "Loyal Customers" # Buy regularly and bought recently

        elif r["R_Score"] >=2 and r["F_Score"] <= 2 :
            return "Promising / Recent" #Newer buyers with potential to become loyal

        elif r["R_Score"] == 1 and r["F_Score"] >= 3 :
            return "At-Risk (Can't Lose)" #Previously high-value buyers who are slipping away

        elif r["R_Score"] == 1 and r["F_Score"] == 1 :
            return "Lost Customers" #Bought once a long time ago and never came back

        return "Needs Attention"
    rfm["Segment"] = rfm.apply(assign_segment,axis=1)
    

    return rfm

#this function identifies each customer's "birth month" (their very first purchase month
#then Calculates period_number (how many months elapsed between their first order month and subsequent order months)
#and Creates a count matrix (cohort_pivot) and divides every row by its initial starting size (Month 0) to compute retention percentages (retention_matrix)'''
def compute_cohort_matrix(engine) :
    query = """
    Select
        customer_id,
        order_timestamp
    FROM orders 
    WHERE order_status = 'Completed'
    """ 

    df = pd.read_sql(query, engine)
    
    df["order_timestamp"] = pd.to_datetime(df["order_timestamp"])

    df["order_month"] = df["order_timestamp"].dt.to_period("M")
    df["cohort"] = df.groupby("customer_id")["order_timestamp"].transform("min").dt.to_period("M")

    

    cohort_group = df.groupby(["cohort" , "order_month"]).agg(n_customers=("customer_id","nunique")).reset_index()
    cohort_group["period_number"] = (cohort_group["order_month"]-cohort_group["cohort"]).apply(lambda x:x.n)

    

    cohort_pivot = cohort_group.pivot(index="cohort",columns="period_number",values="n_customers")
    cohort_size = cohort_pivot.iloc[:,0]
    retention_matrix = cohort_pivot.divide(cohort_size , axis =0) *100

    cohort_pivot.index = cohort_pivot.index.astype(str)
    retention_matrix.index = retention_matrix.index.astype(str)
    retention_matrix.columns = retention_matrix.columns.astype(str)

    

    return cohort_pivot , retention_matrix


# Performs a Pareto (80/20 Rule) Analysis on products to identify top revenue generators.
def compute_pareto_analysis(engine) :
    query = """
    SELECT 
        p.product_name,
        p.category,
        SUM(oi.quantity * oi.item_price) AS total_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'Completed'
    GROUP BY p.product_name , p.category
    ORDER BY total_revenue DESC
    """ 
    df = pd.read_sql(query , engine)
    
    df["cum_revenue"] = df["total_revenue"].cumsum()
    total_rev = df["total_revenue"].sum()
    df["cum_pct"] = (df["cum_revenue"]/total_rev) * 100
    

    return df 

def analyze_trend_insights(df_trend) :
    if df_trend.empty :
        return "No revenue data available."

    peak_row = df_trend.loc[df_trend["Gross_Revenue"].idxmax()]
    latest_row= df_trend.iloc[-1]
    first_row = df_trend.iloc[0]

    insight = (
        f"*Revenue Summary:** Sales started at **${first_row['Gross_Revenue']:,.2f}**  in  {first_row['Month']} "
        f"and reached a peak of **${peak_row['Gross_Revenue']:,.2f}** in **{peak_row['Month']}**. "
        f"The most recent recorded monthly revenue is **${latest_row['Gross_Revenue']:,.2f}**."
    )
    return insight

def analyze_rfm_insights(rfm_df) :
    if rfm_df.empty :
        return "No customer segmentation data available."

    total_cust = len(rfm_df)
    top_seg = rfm_df["Segment"].value_counts().idxmax()
    top_seg_count = rfm_df["Segment"].value_counts().max()
    top_seg_pct = (top_seg_count/total_cust)*100

    champions_pct = (len(rfm_df[rfm_df["Segment"]=="Champions"])/total_cust)*100
    at_risk_pct = (len(rfm_df[rfm_df["Segment"].isin(["At-Risk (Can't Lose)" , "Lost Customers"])])/total_cust)*100


    insight = (
        f"**Segment Summary: ** The largest customer segment is **{top_seg}** "
        f"making up **{top_seg_pct:.1f}%** ({top_seg_count:,}) of total buyers. "
        f"High-value **Champions** represnts **{champions_pct:.1f}%** of your base , while **{at_risk_pct:.1f}%** "
        f"of customers fall into **At-Risk** or **Lost** categories and require re-engagement."
    )
    return insight

def analyze_cohort_insights(retention_matrix) :
    if retention_matrix.empty or retention_matrix.shape[1] < 2:
        return "Insufficient cohort historical length."

    m1_avg = retention_matrix.iloc[:,1].mean()
    m3_avg = retention_matrix.iloc[:, 3].mean() if retention_matrix.shape[1] > 3 else 0.0

    insight = (
        f"**Cohort Summary : ** On average across all cohorts , **{m1_avg:.1f}%** of first-time buyers "
        f"return to place a second order within **1 month** By **Month 3** , average customer retention stands at **{m3_avg:.1f}%**."
    )
    return insight

def analyze_pareto_insights(df_pareto) :
    if df_pareto.empty :
        return "No sales data available for product breakdown."

    top_prod = df_pareto.iloc[0]
    total_rev = df_pareto["total_revenue"].sum()
    top_pct = (top_prod["total_revenue"]/total_rev)*100

    top_80_count = len(df_pareto[df_pareto["cum_pct"] <= 80]) + 1
    total_prods = len(df_pareto)

    insight = (
        f"**Pareto Summary:** Top seller ** {top_prod['product_name']}** generated **${top_prod['total_revenue']:,.2f}**, "
        f"accounting for **{top_pct:.1f}%** of total gross revenue alone. "
        f"Overall , just **{top_80_count} out of {total_prods} products** drive **80%** of total buisness revenue."
    )
    return insight

def analyze_churn_insights(feat_imp) :
    if feat_imp.empty :
        return "No Feature importance available"

    top_feat = feat_imp.iloc[0]
    second_feat = feat_imp.iloc[1]

    insight = (
        f"**Automated Model Summary:** The strongest predictor of customer churn is **{top_feat['feature']}** "
        f"(contributing **{top_feat['importance']*100:.1f}%** to model decisions), followed by **{second_feat['feature']}** "
        f"(**{second_feat['importance']*100:.1f}%**)."
    )
    return insight