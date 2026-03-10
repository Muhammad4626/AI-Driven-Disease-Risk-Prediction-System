import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

# Data setup
data = {
    "target": ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"],
    "mae": [1.662601914, 1.244961728, 0.173116854],
    "rmse": [2.914247216, 1.905555328, 0.276698619],
    "r2": [0.908954621, 0.859586501, 0.552079522]
}
df = pd.DataFrame(data)
df['target'] = df['target'].str.replace('_Risk_next_week', '').str.replace('_', ' ')

#setup plotting
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
metrics = [('mae', 'MAE (Lower is Better)', 'Blues_r'), 
           ('rmse', 'RMSE (Lower is Better)', 'Reds_r'), 
           ('r2', '$R^2$ Score (Higher is Better)', 'Greens')]

for i, (col, title, palette) in enumerate(metrics):
    ax = axes[i]
    sns.barplot(data=df, y='target', x=col, palette=palette, ax=ax)
    
    #add precise values next to bars
    for p in ax.patches:
        width = p.get_width()
        ax.text(width + (width * 0.02), p.get_y() + p.get_height()/2, 
                f'{width:.3f}', va='center', fontsize=12, fontweight='bold')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("")
    
    #force the R2 axis to show 0.1 increments up to 1.0
    if col == 'r2':
        ax.set_xlim(0, 1.1) # Extra space for label
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))

plt.tight_layout()
plt.show()