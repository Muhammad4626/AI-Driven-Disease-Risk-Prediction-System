import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the results CSV (or create manually)
data = {
    "target": ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"],
    "mae": [1.9727, 1.6591, 0.1753],
    "rmse": [3.4663, 2.5222, 0.2635],
    "r2": [0.8728, 0.7614, 0.4170]
}

df = pd.DataFrame(data)

# Set plot style
sns.set(style="whitegrid", palette="muted", font_scale=1.1)

# Create a figure with 3 subplots for MAE, RMSE, R2
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# MAE
sns.barplot(x="target", y="mae", data=df, ax=axes[0])
axes[0].set_title("Mean Absolute Error")
axes[0].set_xlabel("")
axes[0].set_ylabel("MAE")
axes[0].tick_params(axis='x', rotation=30)

# RMSE
sns.barplot(x="target", y="rmse", data=df, ax=axes[1])
axes[1].set_title("Root Mean Squared Error")
axes[1].set_xlabel("")
axes[1].set_ylabel("RMSE")
axes[1].tick_params(axis='x', rotation=30)

# R2
sns.barplot(x="target", y="r2", data=df, ax=axes[2])
axes[2].set_title("R² Score")
axes[2].set_xlabel("")
axes[2].set_ylabel("R²")
axes[2].tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.show()