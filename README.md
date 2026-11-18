# E-Commerce Analytics & Intelligence Engine

An end-to-end e-commerce analytics project that turns transactional data into customer segments, retention analysis, revenue concentration insights, and churn-risk predictions.

## Why I Built This

Most e-commerce dashboards stop at surface-level metrics such as revenue, orders, and average order value. I wanted to build something that connects those numbers to **customer behavior and retention risk**.

The project combines transactional ETL with **RFM segmentation, cohort retention, Pareto 80/20 analysis, and predictive churn modeling** so the same data can support both business reporting and deeper customer analysis.

## Technical Architecture

```text
Synthetic / Raw CSV Data
        │
        ▼
generate_data.py
Synthetic customers, products, orders & order items
with controlled data anomalies
        │
        ▼
etl_pipeline.py
Cleaning → validation → normalization → SQLite
        │
        ├──────────────► analytics.py
        │                KPIs
        │                RFM segmentation
        │                Cohort retention
        │                Pareto analysis
        │                Automated insights
        │
        └──────────────► ml_models.py
                         Feature engineering
                         Random Forest churn model
                         ROC-AUC / classification metrics
                         Feature importance
        │
        ▼
app.py
Streamlit + Plotly dashboard
```

### 1. Synthetic Data Generation — `generate_data.py`

Creates a reproducible e-commerce dataset using Faker, NumPy, and Python's random module. The generator produces customers, products, orders, and order items, while intentionally injecting common data-quality problems such as:

- Duplicate order-item records
- Missing order timestamps
- Negative item prices
- Completed, refunded, and cancelled orders

The defaults generate **1,000 customers and 10,000 orders**.

### 2. Ingestion & ETL — `etl_pipeline.py`

The pipeline checks for the raw CSV files and generates them when they are missing. It then:

- Removes duplicate `order_item_id` and `order_id` records
- Drops orders with missing timestamps
- Converts timestamp fields to datetime
- Filters invalid prices and quantities
- Loads customers, products, orders, and order items into the database

The default connection is SQLite through SQLAlchemy. The accompanying `schema.sql` defines primary keys, foreign keys, and indexes for the relational model.

### 3. Analytics Engine — `analytics.py`

The analytical layer builds the main business metrics from completed orders:

- **Executive KPIs:** revenue, completed orders, unique buyers, and AOV
- **RFM:** Recency, Frequency, and Monetary scoring using Pandas `qcut`
- **Customer segments:** Champions, Loyal Customers, Promising / Recent, At-Risk, Lost Customers, and Needs Attention
- **Cohort retention:** monthly customer cohorts and retention percentages by months since first purchase
- **Pareto analysis:** cumulative product revenue contribution
- **Text insights:** converts analytical outputs into short dashboard summaries

### 4. Churn Modeling — `ml_models.py`

Customer-level features are built from transactional history, including:

- Customer tenure
- Total orders
- Refunded orders
- Total spend
- Acquisition channel

Categorical acquisition channels are one-hot encoded, and a **Random Forest Classifier** is trained to predict churn. Churn is defined as more than **90 days of inactivity** in the available transaction history. The model reports ROC-AUC, classification metrics, and feature importance.

Importantly, `days_since_last_order` is excluded from the feature set because it is directly used to define the churn target.

### 5. Dashboard — `app.py`

The Streamlit application presents five analytical views:

1. Executive Performance
2. RFM Customer Segmentation
3. Cohort Retention
4. Pareto Revenue Analysis
5. ML Churn Prediction

Plotly is used for the revenue trend, segmentation charts, retention heatmap, Pareto visualization, and churn feature-importance chart. The ETL pipeline is also triggered automatically if the database is not initialized.

## Business & Industry Use Case

### Targeted Retention
RFM segments make it possible to distinguish high-value **Champions** from **At-Risk** or **Lost** customers, supporting more targeted retention campaigns instead of treating the entire customer base the same way.

### Product Strategy
Pareto analysis shows how concentrated revenue is across the product catalog, helping identify the small group of products responsible for a large share of sales.

### Proactive Churn Prevention
The churn model ranks customers by learned behavioral patterns and exposes the features most associated with churn, giving customer-success or marketing teams a starting point for re-engagement strategies.

## Technical Challenges & What I Fixed

### 1. Churn Model Data Leakage
During an earlier modeling iteration, `days_since_last_order` was included as a feature even though churn itself was defined using the same field. That made the model learn the target definition instead of genuine customer behavior.

**Fix:** removed `days_since_last_order` from `X`, leaving behavioral features such as tenure, spend, refunds, orders, and acquisition channel.

### 2. Cohort Retention Division Issues
The cohort pivot can contain missing periods, which makes retention calculations and index/column handling awkward.

**Fix:** standardized cohort labels, explicitly converted the matrix index/columns to strings, and used Pandas `.divide(..., axis=0)` to normalize each cohort against its starting size.

### 3. Dirty Input Data
The synthetic generator deliberately creates duplicate records, missing timestamps, and negative prices to simulate imperfect source data.

**Fix:** the ETL layer deduplicates IDs, removes orders without timestamps, and keeps only positive prices and quantities before loading the database.

## Future Enhancements

The current project is intentionally focused on the core analytics pipeline. Some practical next steps would be:

- **PostgreSQL deployment:** Move beyond the default SQLite setup for a more production-oriented database environment.
- **Incremental ETL:** Process only new or changed transactions instead of rebuilding the database on each run.
- **Model improvement:** Add cross-validation, hyperparameter tuning, and better class-imbalance handling for the churn classifier.
- **Customer-level churn scoring:** Store and display predicted churn probabilities for individual customers rather than only model metrics and feature importance.
- **Automated pipeline scheduling:** Run ingestion, analytics, and model scoring on a scheduled basis.
- **Dashboard controls:** Add filters for date range, product category, acquisition channel, and customer segment.
- **Data validation layer:** Add stronger schema and quality checks before loading data into the database.

## Project Structure

```text
.
├── app.py                  # Streamlit dashboard
├── analytics.py            # KPIs, RFM, cohorts, Pareto & insights
├── etl_pipeline.py         # Data ingestion and cleaning
├── generate_data.py        # Synthetic data generator
├── ml_models.py            # Churn model
├── schema.sql              # Relational database schema
├── requirements.txt        # Python dependencies
└── data_raw/               # Generated CSV datasets
```



## Quickstart

```bash
pip install -r requirements.txt
python etl_pipeline.py
streamlit run app.py
```



## Tech Stack

**Python · Pandas · NumPy · SQLAlchemy · SQLite · scikit-learn · Plotly · Streamlit · Faker**

## Author

**Rohit Kumar**

Data Analytics / Engineering portfolio project focused on Python, SQL, ETL pipelines, customer analytics, and applied machine learning.

## License

This project is licensed under the **MIT License**.

See the `LICENSE` file for the full license text.

