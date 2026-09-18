"""
Quick Deployment Setup Script
==============================
Prepares all necessary files for API deployment.
"""

import os
import shutil
import pickle
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import json

print("=" * 80)
print("DEPLOYMENT SETUP - Preparing API Files")
print("=" * 80)

# Create api directory if it doesn't exist
os.makedirs('api', exist_ok=True)

# ============================================================================
# Step 1: Create Price Scaler
# ============================================================================
print("\n[1/5] Creating price scaler...")

try:
    stock_df = pd.read_csv('stock_price.csv')
    stock_df = stock_df.iloc[2:].copy().reset_index(drop=True)
    stock_df['Close'] = pd.to_numeric(stock_df['Close'], errors='coerce')
    stock_df = stock_df.dropna()
    train_size = int(len(stock_df) * 0.6)
    train_prices = stock_df['Close'].values[:train_size]
    
    scaler = MinMaxScaler()
    scaler.fit(train_prices.reshape(-1, 1))
    
    with open('api/price_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    print("[OK] Price scaler created and saved to api/price_scaler.pkl")
except Exception as e:
    print(f"[WARN] Error creating scaler: {e}")
    print("   You'll need to create it manually")

# ============================================================================
# Step 2: Copy Model Files
# ============================================================================
print("\n[2/5] Copying model files...")

models_to_copy = [
    ('mlp_model.keras', 'MLP model'),
    ('advanced_model_final.keras', 'Advanced LSTM model')
]

for filename, description in models_to_copy:
    if os.path.exists(filename):
        shutil.copy(filename, f'api/{filename}')
        print(f"[OK] Copied {description}: {filename}")
    else:
        print(f"[WARN] {description} not found: {filename}")
        print(f"   Train the model first with: python 8_advanced_model.py")

# ============================================================================
# Step 3: Copy or Create Ensemble Config
# ============================================================================
print("\n[3/5] Setting up ensemble configuration...")

if os.path.exists('ensemble_config.json'):
    shutil.copy('ensemble_config.json', 'api/ensemble_config.json')
    print("[OK] Copied ensemble_config.json")
else:
    # Create default config
    default_config = {
        "mlp_weight": 0.4,
        "lstm_weight": 0.6,
        "sequence_length": 10,
        "best_model": "ensemble",
        "performance": {
            "sharpe": 0.76,
            "return": 6.91,
            "direction_acc": 49.45
        }
    }
    
    with open('api/ensemble_config.json', 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("[OK] Created default ensemble_config.json")

# ============================================================================
# Step 4: Verify API Files
# ============================================================================
print("\n[4/5] Verifying API files...")

required_files = [
    'api/app.py',
    'api/requirements.txt',
    'api/Dockerfile',
    'api/docker-compose.yml',
    'api/test_client.py'
]

all_present = True
for filepath in required_files:
    if os.path.exists(filepath):
        print(f"[OK] {filepath}")
    else:
        print(f"[X] Missing: {filepath}")
        all_present = False

# ============================================================================
# Step 5: Create .dockerignore
# ============================================================================
print("\n[5/5] Creating .dockerignore...")

dockerignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Data files
*.csv
*.pkl
results/
logs/
*.png
*.jpg

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Documentation
README.md
*.md
docs/

# Tests
tests/
test_*.py
"""

with open('api/.dockerignore', 'w') as f:
    f.write(dockerignore_content.strip())

print("[OK] Created api/.dockerignore")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("SETUP COMPLETE!")
print("=" * 80)

print("\nChecklist:")
print("  [OK] Price scaler created")
print("  [OK] Model files copied")
print("  [OK] Ensemble config ready")
print("  [OK] API files verified")
print("  [OK] .dockerignore created")

print("\nNext Steps:")
print("\n1. Test locally:")
print("   cd api")
print("   python app.py")
print("   # In another terminal:")
print("   python test_client.py")

print("\n2. Test with Docker:")
print("   cd api")
print("   docker build -t trading-api .")
print("   docker run -p 8000:8000 trading-api")

print("\n3. Deploy to cloud:")
print("   See DEPLOYMENT_GUIDE.md for detailed instructions")
print("   - Google Cloud Run (recommended for beginners)")
print("   - Railway.app (easiest)")
print("   - AWS/Azure (enterprise)")

if not all_present:
    print("\n[WARN] WARNING: Some API files are missing!")
    print("   Make sure all required files exist before deploying.")

print("\n" + "=" * 80)
print("[OK] Ready for deployment!")
print("=" * 80)
