import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report
)

from xgboost import XGBClassifier
import shap
import joblib


INPUT_FILE = "data/clinical/training_dataset.csv"

MODEL_FILE = "ml/xgboost_variant_model.pkl"
FEATURES_FILE = "ml/model_features.pkl"
SHAP_FILE = "ml/shap_values.csv"


# --------------------------------------------------
# 1. Load dataset
# --------------------------------------------------

print("Loading training dataset...")

df = pd.read_csv(INPUT_FILE)

features = [
    "af_tgp",
    "af_exac",
    "af_esp",
    "ref_length",
    "alt_length"
]

X = df[features]
y = df["label"]


print(f"Total records: {len(df):,}")
print(f"Pathogenic: {(y == 1).sum():,}")
print(f"Benign: {(y == 0).sum():,}")


# --------------------------------------------------
# 2. Train/test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))


# --------------------------------------------------
# 3. Impute missing values
# --------------------------------------------------

imputer = SimpleImputer(strategy="median")

X_train = pd.DataFrame(
    imputer.fit_transform(X_train),
    columns=features
)

X_test = pd.DataFrame(
    imputer.transform(X_test),
    columns=features
)


# --------------------------------------------------
# 4. Handle class imbalance
# --------------------------------------------------

negative = (y_train == 0).sum()
positive = (y_train == 1).sum()

scale_pos_weight = negative / positive

print("\nScale positive weight:", scale_pos_weight)


# --------------------------------------------------
# 5. Train XGBoost
# --------------------------------------------------

model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    random_state=42
)


print("\nTraining XGBoost...")

model.fit(
    X_train,
    y_train
)


# --------------------------------------------------
# 6. Predictions
# --------------------------------------------------

probabilities = model.predict_proba(X_test)[:, 1]

predictions = (
    probabilities >= 0.5
).astype(int)


# --------------------------------------------------
# 7. Evaluation
# --------------------------------------------------

accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    probabilities
)

pr_auc = average_precision_score(
    y_test,
    probabilities
)


print("\n========== MODEL RESULTS ==========")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"PR-AUC   : {pr_auc:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        target_names=[
            "Benign",
            "Pathogenic"
        ],
        zero_division=0
    )
)


# --------------------------------------------------
# 8. Save model
# --------------------------------------------------
joblib.dump(
    model,
    MODEL_FILE
)

joblib.dump(
    features,
    FEATURES_FILE
)

joblib.dump(
    imputer,
    "ml/imputer.pkl"
)


print("\nModel saved to:")
print(MODEL_FILE)


# --------------------------------------------------
# 9. SHAP explanation
# --------------------------------------------------

print("\nCalculating SHAP values...")

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(X_test)

shap_df = pd.DataFrame(
    shap_values,
    columns=features
)

shap_df.to_csv(
    SHAP_FILE,
    index=False
)

print("SHAP values saved to:")
print(SHAP_FILE)

print("\nTop features by mean absolute SHAP:")

importance = (
    shap_df.abs()
    .mean()
    .sort_values(ascending=False)
)

print(importance)