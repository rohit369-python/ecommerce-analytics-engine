import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report , roc_auc_score
import os 



def train_churn_model(engine) :
    query = """
    SELECT 
        c.customer_id,
        c.acquisition_channel,
        MIN(o.order_timestamp) AS first_order,
        MAX(o.order_timestamp) AS last_order,
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(CASE WHEN o.order_status = 'Refunded' THEN 1 ELSE 0 END) as refunded_orders,
        SUM(oi.quantity * oi.item_price) as total_spend
        
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id , c.acquisition_channel
    """
    df = pd.read_sql(query,engine)
    df["first_order"] = pd.to_datetime(df["first_order"])
    df["last_order"] = pd.to_datetime(df["last_order"])

    max_date = df["last_order"].max()
    df["days_since_last_order"] = (max_date-df["last_order"]).dt.days
    df["customer_tenure_days"] = (df["last_order"] - df["first_order"]).dt.days

    # definig churn : inactive for <90 days
    df["is_churned"] = (df["days_since_last_order"]>90).astype(int)

    # One-Hot Encoding Categorical Data
    df_encoded = pd.get_dummies(df,columns=["acquisition_channel"],drop_first=True)

    

    # Filters out metadata, raw dates, and non-predictive identifiers (customer_id, first_order, last_order..etc).
    features = [c for c in df_encoded.columns if c not in ["customer_id" , "first_order","last_order","is_churned","days_since_last_order"]]
    X = df_encoded[features]
    y = df_encoded["is_churned"]

    if y.nunique() < 2 :
        return None , None , "Insufficient class diversity for churn modeling."

    X_train , X_test , y_train , y_test = train_test_split(X,y,test_size=0.25 , random_state=42)

    model = RandomForestClassifier(n_estimators=100 , random_state=42)
    model.fit(X_train,y_train)

    #predicts binary class labels (0 for active, 1 for churned) for each test customer.
    preds = model.predict(X_test)

    #returns predicted continuous probabilities ranging from 0.0 to 1.0. [:, 1] extracts the probability of belonging to Class 1 (churned).
    probs = model.predict_proba(X_test)[:,1]

    metrics = {
        "roc_auc" : round(roc_auc_score(y_test,probs),3), #evaluates how effectively the model ranks churned customers higher than non-churned customers
        "report" : classification_report(y_test,preds , output_dict=True) #computes Precision, Recall, and F1-score for both classes
    }

    # measuring how much each input column contributed to decreasing impurity (decision uncertainty)
    feature_importance = pd.DataFrame({
        "feature" : features ,
        "importance" : model.feature_importances_
    }).sort_values("importance" ,ascending=False)

    return model , metrics , feature_importance