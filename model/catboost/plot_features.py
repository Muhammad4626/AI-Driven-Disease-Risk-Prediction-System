import pandas as pd
import matplotlib.pyplot as plt
import os

MALARIA_CSV = "outputs/models/feature_importance_Malaria_Risk_next_week_20251208T235307Z.csv"
AD_CSV = "outputs/models/feature_importance_AD_Risk_next_week_20251208T235307Z.csv"
TYPHOID_CSV = "outputs/models/feature_importance_Typhoid_Risk_next_week_20251208T235307Z.csv"


def plot_graph(csv_path, title):
    df = pd.read_csv(csv_path)
    df = df.head(10)

    feature = df["feature"]
    importance = df["importance"]

    plt.figure()
    plt.bar(feature, importance)
    plt.title(title)
    plt.xlabel("Top 10 Features")
    plt.ylabel("Importance")
    plt.grid(True)
    plt.xticks(rotation=30)
    plt.show()


plot_graph(MALARIA_CSV, "Malaria Risk Next Week: Top 10 Features")
plot_graph(AD_CSV, "AD Risk Next Week: Top 10 Features")
plot_graph(TYPHOID_CSV, "Typhoid Risk Next Week: Top 10 Features")

print("Top 10 feature importance graphs displayed successfully.")
