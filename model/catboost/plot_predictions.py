import pandas as pd
import matplotlib.pyplot as plt
import os

MALARIA_CSV = "outputs/models/preds_Malaria_Risk_next_week_20260301T195115Z.csv"
AD_CSV = "outputs/models/preds_AD_Risk_next_week_20260301T195115Z.csv"
TYPHOID_CSV = "outputs/models/preds_Typhoid_Risk_next_week_20260301T195115Z.csv"


def plot_graph(csv_path, title):
    df = pd.read_csv(csv_path)

    y_true = df["y_true"]
    y_pred = df["y_pred"]

    plt.figure()
    plt.plot(y_true.values, label="Actual")
    plt.plot(y_pred.values, label="Predicted")
    plt.title(title)
    plt.xlabel("Test Samples")
    plt.ylabel("Risk Value")
    plt.legend()
    plt.grid(True)
    plt.show()


plot_graph(MALARIA_CSV, "Malaria Risk Next Week: Actual vs Predicted")
plot_graph(AD_CSV, "AD Risk Next Week: Actual vs Predicted")
plot_graph(TYPHOID_CSV, "Typhoid Risk Next Week: Actual vs Predicted")

print("All three prediction graphs displayed successfully.")
