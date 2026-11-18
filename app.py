import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os 



from etl_pipeline import run_etl_pipeline
from analytics import (
    get_db_connection,
    compute_executive_kpis,
    compute_rfm_segmentation,
    compute_cohort_matrix,
    compute_pareto_analysis,
    analyze_trend_insights,
    analyze_rfm_insights,
    analyze_cohort_insights,
    analyze_pareto_insights,
    analyze_churn_insights
)

from ml_models import train_churn_model 

st.set_page_config(page_title = "E-Commerce Analytics & Intelligence Engine",layout="wide")

st.title("⚡ E-Commerce Analytics & Intelligence Engine")
st.markdown("Production-Ready Data Architecture: Ingestion , SQL Analytics , RFM Cohorts and Predictive Models")

# setting connection to database
DB_URL = "sqlite:///ecommerce_analytics.db"
engine = get_db_connection(DB_URL)

try : 
    kpi = compute_executive_kpis(engine)
except Exception :
    with st.spinner("Intializing schema & executing ETL pipeline...") :
        run_etl_pipeline(db_url=DB_URL)
    kpi = compute_executive_kpis(engine)

tabs = st.tabs(["📊 Executive Overview", "🎯 RFM Segmentation", "🗓️ Cohort Retention", "📈 Pareto Analysis", "🔮 ML Churn Prediction"])

# Tab 1 : Executive Overview
with tabs[0] :
    st.header("Executive Performance Dashboard")
    col1 , col2 , col3 , col4 = st.columns(4)
    col1.metric("Total Revenue" , f"${kpi['Total Revenue']:,.2f}")
    col2.metric("Total Completed Orders" , f"{kpi['Total Orders']:,}")
    col3.metric("Unique Customer Base" , f"{kpi['Unique Buyers']:,}")
    col4.metric("Average Order Value" , f"${kpi['Average Order Value (AOV)']:,.2f}")

    st.markdown("---")
    st.subheader("Monthly Revenue Trend")
    query_trend = """
    SELECT 
        DATE(o.order_timestamp , 'start of month') as Month,
        SUM(oi.quantity * oi.item_price) as Gross_Revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY Month
    ORDER BY Month ASC
    """

    df_trend = pd.read_sql(query_trend,engine)
    

    fig_trend = px.line(df_trend , x = "Month" , y = "Gross_Revenue" ,title="Gross Revenue Trajectory" ,markers=True)
    st.plotly_chart(fig_trend,use_container_width=True)

    st.info(analyze_trend_insights(df_trend))

# Tab 2 : RFM Segmentation
with tabs[1] :
    st.header("Customer Segmentation (Recency, Frequency & Monetary Analysis)")
    rfm_df = compute_rfm_segmentation(engine)

    col_a , col_b = st.columns([1,2])

    with col_a :
        st.subheader("Segment Volume Distribution")
        seg_counts = rfm_df["Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment" , "Count"]
        fig_pie = px.pie(seg_counts,names="Segment",values="Count",hole=0.4,color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie , use_container_width=True)

    with col_b :
        st.subheader("Recency vs Monetary Distribution")
        fig_scatter = px.scatter(
            rfm_df , x = "Recency" , y = "Monetary" , color = "Segment",
            size = "Frequency" , hover_data=["customer_id"],
            title = "Customer Distribution by Recency and Value"
        )
        st.plotly_chart(fig_scatter,use_container_width=True)

    st.info(analyze_rfm_insights(rfm_df))
    st.dataframe(rfm_df.head(50) , use_container_width=True)

# Tab 3 : Cohort Retention
with tabs[2] :
    st.header("Monthly Customer Retention Heatmap")
    counts , retention = compute_cohort_matrix(engine)

    fig_heat = px.imshow(
        retention , 
        labels = dict(x="Months Since First Purchase", y = "Cohort Month",color="Retention Rate (%)"),
        text_auto = ".1f",
        color_continuous_scale="Blues",
        aspect = "auto"
    )
    st.plotly_chart(fig_heat , use_container_width=True)

    st.info(analyze_cohort_insights(retention))

# Tab 4 : Pareto 80/20 Analysis
with tabs[3]  :
    st.header("Pareto Analysis (Revenue Concentration)")
    df_pareto = compute_pareto_analysis(engine)

    fig_pareto = px.bar(df_pareto , x = "product_name" , y = "total_revenue" , title = "Product Revenue Contribution")
    fig_pareto.add_trace(go.Scatter(x=df_pareto["product_name"],y = df_pareto["cum_pct"],yaxis="y2" ,name="Cumulative %",line = dict(color="red",width=2)))

    fig_pareto.update_layout(
        yaxis2 = dict(title= "Cumulative %" ,overlaying ="y",side="right",range=[0,105]),
        xaxis =dict(tickangle = -45)
    )
    st.plotly_chart(fig_pareto , use_container_width=True)

    st.info(analyze_pareto_insights(df_pareto))

# Tab 5 : Churn Model
with tabs[4] :
    st.header("Machine Learning : Churn Classifier")
    if st.button("Train Churn Prediction Model"):
        with st.spinner("Training Random Forest Classifier..."):
            model,metrics,feat_imp = train_churn_model(engine)
            if metrics :
                st.success(f"Model Trained Successfully! ROC-AUC Score : {metrics['roc_auc']}")
                st.subheader("Feature Importance")
                fig_feat = px.bar(feat_imp, x="importance" , y="feature",orientation="h" , title="Predictive Drivers of Churn")
                st.plotly_chart(fig_feat,use_container_width=True)

                st.info(analyze_churn_insights(feat_imp))
                