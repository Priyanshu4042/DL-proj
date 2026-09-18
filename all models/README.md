# FinBERT-LSTM: Advanced Stock Price Prediction

Deep Learning-based stock price prediction using News Sentiment Analysis with **Skip Connections**, **Attention Mechanisms**, and **Production-Ready Deployment**.

📄 **Original Paper:** [arXiv:2211.07392](https://arxiv.org/pdf/2211.07392.pdf)

## 🎯 Project Overview

This project predicts NASDAQ stock prices using:
- **Historical price data** (10-day sequences)
- **News sentiment analysis** (VADER or FinBERT)
- **Advanced LSTM architecture** with skip connections and attention
- **Proper regularization** matched to dataset size

### ✨ New Features (November 2025)

- ✅ **Advanced Model Architecture** - Skip connections, attention, bidirectional LSTM
- ✅ **Proper Train/Val/Test Split** (60/20/20) - No data leakage
- ✅ **Production-Ready API** - FastAPI with Docker deployment
- ✅ **Comprehensive Deployment Guide** - GCP, AWS, Azure, Railway
- ✅ **Critical Bug Fixes** - Double-scaling, data leakage, scaler leakage resolved
- ✅ **Enhanced Metrics** - R², Sharpe ratio, win rate, direction accuracy

---

## 📊 Performance

### Advanced LSTM Model Results:

| Metric | Value | Status |
|--------|-------|--------|
| MAE | 361.98 | ✅ |
| MAPE | 3.01% | ✅ |
| R² | 0.5527 | ✅ |
| **Backtest Return** | **+6.91%** | ✅ |
| **Sharpe Ratio** | **0.76** | ✅ |
| Win Rate | 53.85% | ✅ |
| Max Drawdown | 14.88% | ✅ |

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Train Models

```powershell
# Run advanced model (recommended)
python 8_advanced_model.py

# Or run all models
python run_all.py
```

### 3. Deploy API

```powershell
# Setup deployment files
python setup_deployment.py

# Test locally
cd api
python app.py
# API runs at http://localhost:8000

# Test with client
python test_client.py
```

---

## 📁 Project Structure

### **Core Scripts (Original):**
- `1_news_collection.py` - Fetch news from NYT API
- `2_stock_data_collection.py` - Get stock price data
- `3_news_data_cleaning.py` - Clean and align data
- `4_news_sentiment_analysis.py` - VADER or FinBERT sentiment
- `5_MLP_model.py` - Simple feedforward neural network
- `6_LSTM_model.py` - Basic LSTM model
- `7_lstm_model_bert.py` - LSTM with sentiment integration

### **Advanced Models (New):**
- `8_advanced_model.py` ⭐ - **Skip connections + Attention**
- `9_ensemble_model.py` - Combine MLP + LSTM predictions
- `5_MLP_model_FIXED.py` - Bug-fixed baseline
- `7_lstm_model_bert_FIXED.py` - Bug-fixed BERT-LSTM

### **Deployment:**
- `api/app.py` - FastAPI REST API
- `api/Dockerfile` - Docker container
- `api/docker-compose.yml` - Multi-service deployment
- `api/test_client.py` - API testing
- `setup_deployment.py` - Automated setup

### **Documentation:**
- `FINAL_SUMMARY.md` - Complete results & architecture
- `DEPLOYMENT_GUIDE.md` - Cloud deployment instructions
- `CRITICAL_FIXES_REPORT.md` - Bug fixes & improvements

---

## 🏗️ Model Architecture

### Advanced LSTM (Recommended):

```
Input (10 timesteps × 2 features)
    ↓
Bidirectional LSTM (32 units) ──┐
    ↓                           │ Skip
Bidirectional LSTM (16 units) ←─┘ Connection
    ↓
Attention Layer (learns important timesteps)
    ↓
Dense (16 units, ReLU, L2 reg, Dropout)
    ↓                           │
Dense (8 units, ReLU, L2 reg) ←─┘ Skip Connection
    ↓
Output (1 unit - predicted price)
```

**Key Features:**
- ✅ Skip/Residual connections for gradient flow
- ✅ Attention mechanism for temporal importance
- ✅ L2 regularization (λ=0.001)
- ✅ Dropout (0.2-0.3) to prevent overfitting
- ✅ Learning rate scheduling (ReduceLROnPlateau)
- ✅ Early stopping on validation loss

---

## 📊 Pipeline Workflow

### Option 1: Automated (Recommended)

```powershell
python run_all.py --collect-news --models advanced
```

### Option 2: Manual Steps

```powershell
# Step 1: Collect data
python 1_news_collection.py
python 2_stock_data_collection.py

# Step 2: Clean and align
python 3_news_data_cleaning.py

# Step 3: Sentiment analysis
python 4_news_sentiment_analysis.py --method vader  # Fast
# OR
python 4_news_sentiment_analysis.py --method finbert  # Better accuracy

# Step 4: Train models
python 8_advanced_model.py  # Recommended
python 9_ensemble_model.py  # Ensemble

# Step 5: Deploy
python setup_deployment.py
cd api && python app.py
```

---

## 🐳 Docker Deployment

### Build & Run:

```powershell
cd api

# Build image
docker build -t trading-api .

# Run container
docker run -p 8000:8000 trading-api

# Or use Docker Compose
docker-compose up -d
```

### Access API:
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Predict:** POST http://localhost:8000/predict

---

## ☁️ Cloud Deployment

### Google Cloud Run (Recommended):

```powershell
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/trading-api
gcloud run deploy trading-api --image gcr.io/PROJECT_ID/trading-api
```

### Railway.app (Easiest):

1. Visit https://railway.app
2. Connect GitHub repo
3. Deploy with one click
4. **Cost:** $5/month

### AWS ECS / Azure:

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for detailed instructions.

---

## 🔧 Critical Bug Fixes

### Original Issues (Now Fixed):

1. ❌ **Double-scaling sentiment** → Already in [-1,1], scaled again to [0,1]
   - **Impact:** MAE exploded from 389 → 12,532
   - **Fix:** Use raw sentiment scores

2. ❌ **Data leakage** → Using future sentiment to predict past prices
   - **Fix:** Proper temporal alignment (same time windows)

3. ❌ **Scaler leakage** → Fitted on train+test together
   - **Fix:** Fit scaler on training data only

4. ❌ **No validation set** → Overfitting to test data
   - **Fix:** 60/20/20 train/val/test split

See **[CRITICAL_FIXES_REPORT.md](CRITICAL_FIXES_REPORT.md)** for full analysis.

---

## 📈 API Usage

### Predict Stock Price:

```python
import requests

response = requests.post('http://localhost:8000/predict', json={
    "price_history": [12000, 12050, 12100, 12080, 12120, 
                      12150, 12200, 12180, 12220, 12250],
    "sentiment_history": [0.2, 0.1, -0.1, 0.3, 0.4, 
                         0.2, 0.5, 0.3, 0.6, 0.4]
})

print(response.json())
```

### Response:

```json
{
  "prediction": {
    "ensemble": 12380.45,
    "mlp": 12350.20,
    "lstm": 12400.10
  },
  "current_price": 12250.00,
  "predicted_change": 130.45,
  "predicted_change_pct": 1.06,
  "signal": "BUY",
  "confidence": 1.06,
  "timestamp": "2025-11-04T22:30:00"
}
```

---

## ⚠️ Known Limitations

1. **Small dataset** (503 samples) - Need 1500+ for robust learning
2. **Direction accuracy ~49%** - Close to random (needs improvement)
3. **VADER sentiment** - Too simplistic for financial news
4. **Single asset** - Only tested on NASDAQ index
5. **No transaction costs** - Backtest doesn't include fees

### Recommendations:

- 📊 Collect 3-5 years of data (not just 1 year)
- 🔧 Add technical indicators (RSI, MACD, Moving Averages)
- 🧠 Use FinBERT instead of VADER
- 📉 Try classification (up/down) instead of regression
- 📄 Paper trade for 3-6 months before live trading

---

## 📚 Documentation

- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete architecture & results
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step cloud deployment
- **[CRITICAL_FIXES_REPORT.md](CRITICAL_FIXES_REPORT.md)** - Bug analysis & solutions

---

## 🎓 Citation

If you use this work, please cite:

```bibtex
@article{finbert-lstm-2022,
  title={FinBERT-LSTM: Deep Learning based stock price prediction using News Sentiment Analysis},
  author={Your Name},
  journal={arXiv preprint arXiv:2211.07392},
  year={2022}
}
```

---

## 📝 License

See LICENSE file for details.

---

## 🙏 Acknowledgments

- **FinBERT:** ProsusAI/finbert pre-trained model
- **VADER:** NLTK sentiment analysis toolkit
- **FastAPI:** Modern Python web framework
- **TensorFlow/Keras:** Deep learning framework

---

## 🆘 Troubleshooting

### Models not training?
- Check Python version (3.10+ required)
- Verify TensorFlow installation: `python -c "import tensorflow; print(tensorflow.__version__)"`
- Install GPU drivers for faster training

### API won't start?
```powershell
# Check dependencies
cd api
pip install -r requirements.txt

# Verify models exist
ls *.keras
ls ensemble_config.json
ls price_scaler.pkl
```

### Docker build fails?
```powershell
# Clear cache
docker system prune -a

# Rebuild
docker build --no-cache -t trading-api .
```

---

## 🚀 Next Steps

1. ✅ **Train models:** `python 8_advanced_model.py`
2. ✅ **Test API:** `python setup_deployment.py && cd api && python app.py`
3. 🔄 **Collect more data:** Expand to 3-5 years
4. 🔄 **Add features:** Technical indicators, volume, VIX
5. 🔄 **Paper trade:** Validate with real-time data
6. 🔄 **Deploy to cloud:** See DEPLOYMENT_GUIDE.md

---

**Status:** ✅ Production-Ready (for paper trading)  
**Created:** November 4, 2025  
**Maintained by:** [Your Name]

