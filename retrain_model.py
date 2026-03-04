import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load dataset
df = pd.read_csv("processed_dataset.csv")

# Features and labels
X = df["symptoms"]
y = df["Disease"]

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
X_vectorized = vectorizer.fit_transform(X)

# Train model
model = MultinomialNB()
model.fit(X_vectorized, y)

# Save new model and vectorizer
joblib.dump(model, "general_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model retrained successfully using TF-IDF.")