import pandas as pd
import matplotlib.pyplot as plt

# CONFIG
model_name = "Malaria_Risk"
dataset_file = "processed_dataset.csv"
pred_file = f"outputs/models/preds_{model_name}_20251207T215658Z.csv"

# Load predictions
y_pred = pd.read_csv(pred_file).iloc[:, 0]  # predicted values
num_test = len(y_pred)  # 1272

# Load dataset
df = pd.read_csv(dataset_file)
y_test = df[model_name].iloc[-num_test:].reset_index(drop=True)

# Scatter plot
plt.figure(figsize=(6,6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
plt.xlabel("Actual Risk")
plt.ylabel("Predicted Risk")
plt.title(f"{model_name}: Actual vs Predicted")
plt.grid(alpha=0.3)
plt.show()
