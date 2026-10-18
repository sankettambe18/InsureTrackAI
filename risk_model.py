
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

def train_risk_model():
    # Synthetic demonstration data only
    data = {
        "age": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65,
                22, 28, 38, 48, 58, 68],
        "insurance_type": [
            0, 1, 2, 0, 1, 2, 0, 1,
            2, 0, 1, 2, 0, 1, 2, 0
        ],
        "risk_level": [
            "Low", "Low", "Medium", "Low",
            "Medium", "Medium", "Low", "Medium",
            "High", "High", "Low", "Medium",
            "Medium", "High", "High", "High"
        ]
    }

    df = pd.DataFrame(data)

    X = df[["age", "insurance_type"]]
    y = df["risk_level"]

    model = DecisionTreeClassifier(
        max_depth=3,
        random_state=42
    )

    model.fit(X, y)

    return model


def estimate_risk(age, insurance_type):
    model = train_risk_model()

    sample = pd.DataFrame({
        "age": [age],
        "insurance_type": [insurance_type]
    })

    prediction = model.predict(sample)[0]

    return prediction
