import joblib
import pandas as pd

# Load model
model = joblib.load("sepsis_model.pkl")

# Get feature names used during training
feature_names = model.feature_names_in_

print("Model expects these features:")
print(feature_names)

print("\nEnter patient details:")

# Take important inputs
HR = float(input("Heart Rate: "))
Temp = float(input("Temperature: "))
SBP = float(input("Systolic BP: "))
Resp = float(input("Respiratory Rate: "))
O2Sat = float(input("Oxygen Saturation: "))

# Create empty dataframe with correct feature names
input_data = pd.DataFrame(columns=feature_names)

# Fill everything with 0 first
input_data.loc[0] = 0

# Now assign values to correct columns (if they exist)
if "HR" in feature_names:
    input_data.at[0, "HR"] = HR
if "Temp" in feature_names:
    input_data.at[0, "Temp"] = Temp
if "SBP" in feature_names:
    input_data.at[0, "SBP"] = SBP
if "Resp" in feature_names:
    input_data.at[0, "Resp"] = Resp
if "O2Sat" in feature_names:
    input_data.at[0, "O2Sat"] = O2Sat

# Predict probability
risk = model.predict_proba(input_data)[0][1]

print(f"\nSepsis Risk Probability: {risk*100:.2f}%")

if risk > 0.7:
    print("⚠️ HIGH RISK of Sepsis.")
elif risk > 0.4:
    print("⚠️ Moderate Risk.")
else:
    print("Low Risk.")

print("\nNote: Educational AI prediction only.")
