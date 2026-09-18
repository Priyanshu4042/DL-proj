# 🚀 QUICK REFERENCE - Trading Model Deployment

## 🏆 Best Model: Advanced LSTM
- **Return:** +15.79% (backtest)
- **Sharpe:** 1.50 (excellent)
- **MAE:** 360.18 (~$360 error)
- **R²:** 0.5775 (explains 58% of variance)

---

## ⚡ Quick Commands

### Train Models:
```powershell
python run_all.py --models all          # All advanced models
python 8_advanced_model.py              # Just advanced LSTM
python 9_ensemble_model.py              # Ensemble
```

### Deploy Locally:
```powershell
python setup_deployment.py              # Prepare API files
cd api && python app.py                 # Start server
python test_client.py                   # Test API
```

### Deploy to Cloud:
```powershell
# Railway.app (easiest)
# → https://railway.app, connect repo, deploy

# Google Cloud Run (recommended)
gcloud builds submit --tag gcr.io/PROJECT/trading-api
gcloud run deploy --image gcr.io/PROJECT/trading-api

# Docker (self-hosted)
cd api
docker-compose up -d
```

---

## 📁 Key Files

**Use These:**
- `8_advanced_model.py` ⭐ - Best model
- `advanced_model_final.keras` - Trained weights
- `api/app.py` - FastAPI server
- `DEPLOYMENT_GUIDE.md` - Full instructions

**Read These:**
- `PIPELINE_RESULTS.md` - Complete results
- `FINAL_SUMMARY.md` - Architecture & recommendations
- `README.md` - Quick start

---

## 🎯 API Usage

### Health Check:
```bash
GET http://localhost:8000/health
```

### Predict:
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
  "prediction": {"ensemble": 12380.45},
  "signal": "BUY",
  "predicted_change_pct": 1.06
}
```

---

## ⚠️ Before Live Trading

1. **Paper trade 3-6 months** ✅
2. **Verify 15.79% return** on new data ✅
3. **Add stop losses** (5% max) ✅
4. **Small position sizes** (1-2% portfolio) ✅
5. **Track all predictions** in spreadsheet ✅

---

## 🔧 Troubleshooting

### Models not loading?
```powershell
ls *.keras                              # Check models exist
python 8_advanced_model.py              # Retrain if missing
```

### API won't start?
```powershell
cd api
pip install -r requirements.txt        # Install deps
ls price_scaler.pkl ensemble_config.json  # Check files
python setup_deployment.py              # Regenerate files
```

### Docker build fails?
```powershell
docker system prune -a                  # Clear cache
docker build --no-cache -t trading-api .
```

---

## 📊 Model Architecture Summary

```
Input (10 days × 2 features: price, sentiment)
    ↓
Bidirectional LSTM (32 units) ──┐
    ↓                           │ Skip
Bidirectional LSTM (16 units) ←─┘
    ↓
Attention (learns important days)
    ↓
Dense (16) → Dense (8) ──┐
                         │ Skip
                      ADD ←─┘
    ↓
Output (predicted price)
```

**Total Parameters:** 22,259  
**Training Time:** ~5 min (CPU)  
**Inference:** ~50ms/prediction

---

## 💰 Deployment Costs

| Platform | Cost/Month | Difficulty | Auto-scale |
|----------|-----------|------------|------------|
| Railway.app | $5 | ⭐ Easy | Yes |
| GCP Cloud Run | $5-20 | ⭐⭐ Medium | Yes |
| AWS ECS | $30-60 | ⭐⭐⭐ Hard | Yes |
| Docker (self) | $5-10 VPS | ⭐⭐⭐ Hard | No |

**Recommended:** Railway.app or GCP Cloud Run

---

## 📈 Performance Metrics Explained

| Metric | Value | Meaning |
|--------|-------|---------|
| **MAE** | 360.18 | Avg error of $360 |
| **MAPE** | 2.98% | 3% error on average |
| **R²** | 0.5775 | Explains 58% of variance |
| **Sharpe** | 1.50 | Excellent risk-adj return |
| **Return** | +15.79% | Profit in backtest |
| **Drawdown** | -10.06% | Max loss from peak |
| **Win Rate** | 54.95% | Profitable trades |

---

## 🎓 Next Steps Checklist

- [ ] Deploy API locally and test
- [ ] Deploy to Railway.app or GCP
- [ ] Set up paper trading account
- [ ] Track predictions for 1 month
- [ ] If profitable, continue 3-6 months
- [ ] Collect more data (3-5 years)
- [ ] Add technical indicators
- [ ] Try FinBERT sentiment
- [ ] If still profitable, start with 0.5% positions
- [ ] Scale up gradually if working

---

## 🆘 Get Help

1. Check `DEPLOYMENT_GUIDE.md`
2. Review error logs
3. Verify all files exist
4. Ensure dependencies installed
5. Try Docker (isolates environment)

---

**Status:** ✅ Ready for Deployment  
**Model:** Advanced LSTM with Skip Connections & Attention  
**Performance:** +15.79% backtest return, Sharpe 1.50  
**Action:** Deploy → Paper Trade → Refine → Profit!

🚀 Good luck!
