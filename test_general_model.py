import joblib

# Load saved model and vectorizer
model = joblib.load("general_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Test input
user_input = input("Enter symptoms: ").lower()

# Convert to vector
input_vector = vectorizer.transform([user_input])

# Predict
prediction = model.predict(input_vector)[0]

print("Predicted Disease:", prediction)
