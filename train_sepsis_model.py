import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load dataset
data = pd.read_csv("Dataset.csv")

print("Initial shape:", data.shape)

# Drop unnecessary columns
data = data.drop(["Unnamed: 0", "Patient_ID"], axis=1)

# Fill missing values column-wise using forward fill then mean
data = data.ffill()
data = data.fillna(data.mean())

print("After cleaning:", data.shape)

# Separate features and label
X = data.drop("SepsisLabel", axis=1)
y = data["SepsisLabel"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluation
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "sepsis_model.pkl")

print("Model saved successfully.")