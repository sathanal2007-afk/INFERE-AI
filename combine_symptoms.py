print("Script started")
import pandas as pd

# 1. Load your dataset
df = pd.read_csv("disease.csv")   # ← change this if your file name is different

# 2. Find all symptom columns automatically
symptom_columns = [col for col in df.columns if "Symptom" in col]

# 3. Combine them into one single column
df["symptoms"] = df[symptom_columns].fillna("").agg(" ".join, axis=1)

# 4. Convert to lowercase (cleaner for ML)
df["symptoms"] = df["symptoms"].str.lower()

# 5. Save new processed dataset
df.to_csv("processed_dataset.csv", index=False)

print("Symptoms combined successfully.")
