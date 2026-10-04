import os

import joblib
import numpy as np
import pandas as pd
import shap


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "xgboost_variant_model.pkl"
)

FEATURES_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "model_features.pkl"
)

IMPUTER_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "imputer.pkl"
)


# Load saved model and preprocessing
model = joblib.load(MODEL_FILE)
features = joblib.load(FEATURES_FILE)
imputer = joblib.load(IMPUTER_FILE)

# SHAP explainer for the trained XGBoost model
explainer = shap.TreeExplainer(model)


def predict_variant(
    af_tgp,
    af_exac,
    af_esp,
    ref_length,
    alt_length
):
    """
    Run prediction using the trained XGBoost model.

    This uses the exact same feature order and
    median imputation strategy used during training.
    """

    input_data = pd.DataFrame(
        [[
            af_tgp,
            af_exac,
            af_esp,
            ref_length,
            alt_length
        ]],
        columns=features
    )

    # Apply the same imputer used during training
    input_imputed = pd.DataFrame(
        imputer.transform(input_data),
        columns=features
    )

    # Model probability
    probability = float(
        model.predict_proba(input_imputed)[0][1]
    )

    # Classification threshold used during evaluation
    prediction = int(
        probability >= 0.5
    )

    label = (
        "Pathogenic-classified"
        if prediction == 1
        else "Benign-classified"
    )

    # SHAP explanation
    shap_values = explainer.shap_values(
        input_imputed
    )

    # Handle SHAP output safely
    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    contributions = []

    for feature, value in zip(
        features,
        values
    ):
        contributions.append({
            "name": feature,
            "value": float(value),
            "absolute": float(abs(value))
        })

    # Sort by absolute contribution
    contributions.sort(
        key=lambda x: x["absolute"],
        reverse=True
    )

    return {
        "label": label,
        "probability": probability,
        "prediction": prediction,
        "features": contributions
    }