import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for premium look
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.titlesize': 18
})

# Paths
DATA_FILE_PATH = 'notebooks/car-details.csv'
MODEL_PATH = 'app/models/model.joblib'
ASSETS_DIR = 'docs/assets'

os.makedirs(ASSETS_DIR, exist_ok=True)

# 1. Load Data & Model
print("Loading data...")
df = pd.read_csv(DATA_FILE_PATH).drop_duplicates()
df_clean = df.drop(columns=['name', 'model', 'edition'])

X = df_clean.drop(columns='selling_price')
y = df_clean['selling_price']

print("Loading model...")
model = joblib.load(MODEL_PATH)

# Extract preprocessor and regressor
preprocessor = model.named_steps['pre']
regressor = model.named_steps['reg']

# Retrieve numeric column names
num_cols = X.select_dtypes(include='number').columns.tolist()
cat_cols = [col for col in X.columns if col not in num_cols]

# Retrieve categorical column names from OneHotEncoder
encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
cat_features_out = list(encoder.get_feature_names_out(cat_cols))

# Full list of feature names
feature_names = num_cols + cat_features_out

# Get feature importances
importances = regressor.feature_importances_
indices = np.argsort(importances)[::-1]

# Top 10 Features DataFrame
top_n = 10
top_features = [feature_names[i] for i in indices[:top_n]]
top_importances = importances[indices[:top_n]]

# Clean up names for plotting (e.g. company_Maruti -> Company: Maruti)
clean_features = []
for f in top_features:
    if '_' in f and not any(x in f for x in ['km_driven', 'mileage_mpg', 'engine_cc', 'max_power_bhp', 'torque_nm']):
        parts = f.split('_', 1)
        clean_features.append(f"{parts[0].capitalize()}: {parts[1]}")
    else:
        clean_features.append(f.replace('_', ' ').title())

# 2. Plot Feature Importance
print("Generating Feature Importance plot...")
plt.figure(figsize=(10, 6), dpi=150)
colors = sns.color_palette("viridis", top_n)
sns.barplot(x=top_importances, y=clean_features, palette=colors, hue=clean_features, legend=False)
plt.title("Top 10 Feature Importances in Car Price Prediction", pad=20, weight='bold')
plt.xlabel("Relative Importance Score", labelpad=12)
plt.ylabel("Features", labelpad=12)
plt.tight_layout()
plt.savefig(os.path.join(ASSETS_DIR, 'feature_importance.png'), bbox_inches='tight')
plt.close()

# 3. Plot Actual vs Predicted Prices
print("Generating Actual vs Predicted Prices plot...")
predictions = model.predict(X)

plt.figure(figsize=(10, 6), dpi=150)
# Subsample for clearer scatter representation
if len(X) > 2000:
    indices_sub = np.random.choice(len(X), 2000, replace=False)
    y_sub = y.iloc[indices_sub]
    pred_sub = predictions[indices_sub]
else:
    y_sub = y
    pred_sub = predictions

# Log-log scatter plot since car prices span orders of magnitude
sns.scatterplot(x=y_sub, y=pred_sub, alpha=0.4, color='#1f77b4', edgecolor='none')

# Add 45 degree reference line
max_val = max(y.max(), predictions.max())
min_val = min(y.min(), predictions.min())
plt.plot([min_val, max_val], [min_val, max_val], color='#ff7f0e', linestyle='--', linewidth=2, label='Perfect Prediction')

plt.xscale('log')
plt.yscale('log')
plt.title("Actual vs. Predicted Car Selling Prices (Log Scale)", pad=20, weight='bold')
plt.xlabel("Actual Price ($)", labelpad=12)
plt.ylabel("Predicted Price ($)", labelpad=12)
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(ASSETS_DIR, 'model_performance.png'), bbox_inches='tight')
plt.close()

print("Charts successfully generated in docs/assets/ directory!")
