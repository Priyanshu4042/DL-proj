# 🆓 Free 24/7 Deployment Services

## ✅ Recommended Free Options (Always On)

### 🌟 1. **Render.com** (BEST FREE OPTION)
**Why Best:**
- ✅ **Completely FREE** tier available
- ✅ **24/7 uptime** (always on, no sleeping)
- ✅ **750 hours/month free** (enough for 24/7)
- ✅ **Auto-deploy from GitHub**
- ✅ **HTTPS included**
- ✅ **No credit card required**

**Limitations:**
- ⚠️ Spins down after 15 min inactivity (first request takes ~30 sec to wake)
- 512MB RAM (enough for our model)

**Deploy Steps:**
```bash
# 1. Push to GitHub (if not done)
git init
git add .
git commit -m "Trading API"
git push origin main

# 2. Go to render.com
# - Sign up (free, no credit card)
# - New → Web Service
# - Connect GitHub repo "FinBERT-LSTM"
# - Settings:
#   - Name: trading-api
#   - Region: Oregon (US West)
#   - Branch: main
#   - Root Directory: api
#   - Runtime: Docker
#   - Instance Type: Free
# - Click "Create Web Service"

# 3. Wait 5 minutes for build
# You'll get: https://trading-api-xxx.onrender.com
```

**Keep it Awake** (prevent 15-min spin down):
```bash
# Use free cron service like cron-job.org
# Schedule ping every 10 minutes:
curl https://trading-api-xxx.onrender.com/health
```

---

### 🚀 2. **Koyeb** (True Always-On Free)
**Why Good:**
- ✅ **Truly always on** (no cold starts)
- ✅ **FREE tier** with 512MB RAM
- ✅ **Global CDN** (fast worldwide)
- ✅ **Auto-scaling**
- ✅ **HTTPS included**

**Limitations:**
- ⚠️ Requires credit card (won't charge unless you upgrade)
- Free tier: 1 service, 512MB RAM

**Deploy Steps:**
```bash
# 1. Go to koyeb.com
# - Sign up (credit card required but free tier available)
# - Create App → From GitHub
# - Select "FinBERT-LSTM" repo
# - Settings:
#   - Builder: Docker
#   - Dockerfile path: api/Dockerfile
#   - Port: 8000
#   - Instance: Nano (free)
# - Deploy

# You'll get: https://trading-api-xxx.koyeb.app
```

---

### 🐳 3. **Fly.io** (Free with Limits)
**Why Good:**
- ✅ **Always on** (no sleeping)
- ✅ **256MB RAM free** (might be tight)
- ✅ **3 shared CPUs free**
- ✅ **HTTPS + global deployment**
- ✅ **CLI-based deployment**

**Limitations:**
- ⚠️ Requires credit card
- 256MB RAM (our model is 360KB, should work with optimization)

**Deploy Steps:**
```bash
# 1. Install Fly CLI
# Windows PowerShell:
iwr https://fly.io/install.ps1 -useb | iex

# 2. Login and launch
cd api
fly auth login
fly launch

# Answer prompts:
# - App name: trading-api
# - Region: Choose closest
# - Postgres: No
# - Redis: No
# - Deploy: Yes

# You'll get: https://trading-api.fly.dev
```

**Create `fly.toml` in api/ folder:**
```toml
app = "trading-api"
primary_region = "iad"

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false  # Keep always on
  auto_start_machines = true
  min_machines_running = 1     # Always 1 instance

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

---

### 🌐 4. **Railway.app** (Free Trial, Then Cheap)
**Why Include:**
- ✅ **$5 free trial** credit
- ✅ **Always on** (no sleeping)
- ✅ **Easy deploy** (easiest UI)
- ✅ **Best monitoring**

**Limitations:**
- ⚠️ After $5 credit: $5/month (still cheapest)
- ⚠️ Credit card required

**Deploy Steps:**
```bash
# See DEPLOY_RAILWAY.md for detailed steps
# 1. Push to GitHub
# 2. railway.app → Deploy from GitHub
# 3. Done! https://trading-api.railway.app
```

---

### 🔧 5. **Hugging Face Spaces** (FREE Forever)
**Why Interesting:**
- ✅ **Completely FREE**
- ✅ **Always on** (with Docker SDK)
- ✅ **Unlimited usage**
- ✅ **Made for ML models**

**Limitations:**
- ⚠️ Designed for Gradio/Streamlit (need to adapt)
- ⚠️ 16GB storage limit (plenty for our 360KB model)

**Deploy Steps:**
```bash
# 1. Go to huggingface.co
# - Create account (free)
# - New Space → Name: "trading-api"
# - SDK: Docker
# - Create Space

# 2. Clone and push
git clone https://huggingface.co/spaces/YOUR_USERNAME/trading-api
cd trading-api

# 3. Copy your API files
cp -r ../FinBERT-LSTM/api/* .

# 4. Create README.md (required)
cat > README.md << 'EOF'
---
title: Trading API
emoji: 📈
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Trading API with Advanced LSTM
Stock price prediction API using FinBERT sentiment + LSTM.
EOF

# 5. Push
git add .
git commit -m "Deploy trading API"
git push

# You'll get: https://YOUR_USERNAME-trading-api.hf.space
```

---

## 📊 Free Options Comparison

| Platform       | Cost  | Always On? | Cold Start | RAM   | Easy Deploy | Credit Card | Best For           |
|----------------|-------|------------|------------|-------|-------------|-------------|--------------------|
| **Render.com** | FREE  | Yes*       | 30s        | 512MB | ⭐⭐⭐⭐⭐      | No          | **24/7 Testing**   |
| **Koyeb**      | FREE  | Yes        | None       | 512MB | ⭐⭐⭐⭐☆      | Yes         | Production Ready   |
| **Fly.io**     | FREE  | Yes        | None       | 256MB | ⭐⭐⭐☆☆      | Yes         | CLI Users          |
| **Railway**    | $5 trial | Yes     | None       | 8GB   | ⭐⭐⭐⭐⭐      | Yes         | Easiest (then $5/mo)|
| **HF Spaces**  | FREE  | Yes        | 10s        | 16GB  | ⭐⭐⭐☆☆      | No          | ML Models          |

**\*Render.com spins down after 15 min** - Use cron-job.org to ping every 10 min (free)

---

## 🎯 My Recommendation for You

### **For Testing (Paper Trading Validation): Render.com**

```bash
# 1. Deploy to Render (5 minutes)
# - render.com → New Web Service → Connect GitHub
# - Choose "FinBERT-LSTM" → Deploy

# 2. Keep it awake (cron-job.org)
# - cron-job.org → Create account (free)
# - New Cron Job:
#   - Title: Keep Trading API Awake
#   - URL: https://trading-api-xxx.onrender.com/health
#   - Schedule: Every 10 minutes
#   - Save

# 3. Test 24/7
curl https://trading-api-xxx.onrender.com/health
# Should respond instantly (because cron keeps it warm)
```

**Advantages:**
- ✅ **FREE forever**
- ✅ **No credit card**
- ✅ **24/7 available** (with cron pinger)
- ✅ **512MB RAM** (plenty for our model)
- ✅ **Easy UI** (non-technical friendly)

---

## 🤖 Paper Trading Strategy (24/7 Testing)

Since paper trading only works during market hours (9:30 AM - 4:00 PM EST), here's how to use your 24/7 API:

### **Setup:**

1. **Deploy API to Render.com** (always available)
2. **Set up automated testing** (runs 24/7)
3. **Collect predictions during market hours** (9:30 AM - 4:00 PM EST)
4. **Compare with actual prices** (next day open)

### **Automated Testing Script:**

Create `paper_trading_bot.py`:

```python
import requests
import pandas as pd
from datetime import datetime, time
import schedule
import time as time_module

API_URL = "https://trading-api-xxx.onrender.com"

def is_market_hours():
    """Check if US market is open (9:30 AM - 4:00 PM EST)"""
    now = datetime.now()
    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now.time() <= market_close and now.weekday() < 5

def make_prediction():
    """Make daily prediction"""
    if not is_market_hours():
        print(f"{datetime.now()}: Market closed, skipping...")
        return
    
    # Get last 10 days data (you'll need to implement this)
    # For now, using dummy data
    payload = {
        "prices": [12000, 12100, 12050, 12200, 12150, 12300, 12250, 12400, 12350, 12500],
        "sentiments": [0.2, 0.1, 0.3, 0.0, 0.2, 0.4, 0.2, 0.3, 0.1, 0.5],
        "use_ensemble": False
    }
    
    try:
        response = requests.post(f"{API_URL}/predict", json=payload)
        result = response.json()
        
        # Log prediction
        log_entry = {
            "timestamp": datetime.now(),
            "predicted_price": result["predicted_price"],
            "confidence": result["confidence"],
            "model_used": result["model_used"]
        }
        
        # Save to CSV
        df = pd.DataFrame([log_entry])
        df.to_csv("predictions_log.csv", mode='a', header=False, index=False)
        
        print(f"✓ Prediction logged: {result['predicted_price']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")

# Schedule prediction every day at 3:30 PM (before market close)
schedule.every().day.at("15:30").do(make_prediction)

print("🤖 Paper Trading Bot started...")
print("📊 Making predictions daily at 3:30 PM EST")

while True:
    schedule.run_pending()
    time_module.sleep(60)  # Check every minute
```

**Run it 24/7 on your local machine:**
```bash
python paper_trading_bot.py
```

Or deploy this bot to **PythonAnywhere** (free 24/7 Python hosting):
- pythonanywhere.com → Free account
- Upload `paper_trading_bot.py`
- Set as always-running task

---

## 🆓 Free Cron Services (Keep Render Awake)

| Service           | Free Tier           | Setup Time | Best For          |
|-------------------|---------------------|------------|-------------------|
| **cron-job.org**  | Unlimited jobs      | 2 min      | Simple HTTP pings |
| **UptimeRobot**   | 50 monitors         | 3 min      | Uptime monitoring |
| **Freshping**     | 50 checks           | 5 min      | Advanced alerts   |
| **StatusCake**    | 10 monitors         | 3 min      | Status pages      |

**Recommended: cron-job.org**
```
1. Go to cron-job.org
2. Create account (free)
3. New Cron Job:
   - Title: Trading API Health Check
   - URL: https://YOUR_APP.onrender.com/health
   - Execution Schedule: */10 * * * * (every 10 minutes)
4. Save
```

This prevents Render from sleeping! ✅

---

## 💡 Cost Analysis (3 Months Paper Trading)

| Option                    | Cost   | Notes                          |
|---------------------------|--------|--------------------------------|
| **Render.com + Cron**     | $0     | Completely FREE                |
| **Koyeb**                 | $0     | FREE (credit card on file)     |
| **Fly.io**                | $0     | FREE (256MB might be tight)    |
| **Railway**               | $15    | $5/month (best UX)             |
| **HF Spaces**             | $0     | FREE forever                   |

**Winner for 3-6 month testing: Render.com** ✅

---

## 🚀 Quick Start (Deploy in 10 Minutes)

### Option 1: Render.com (Recommended)

```bash
# Step 1: Push to GitHub (if not done)
cd "D:\#EditorCodes\FinBERT-LSTM"
git init
git add .
git commit -m "Trading API ready"
git remote add origin https://github.com/YOUR_USERNAME/FinBERT-LSTM.git
git push -u origin main

# Step 2: Deploy to Render
# Go to: https://render.com
# 1. Sign up (no credit card)
# 2. New → Web Service
# 3. Connect GitHub → Select "FinBERT-LSTM"
# 4. Settings:
#    - Name: trading-api
#    - Region: Oregon
#    - Root Directory: api
#    - Runtime: Docker
#    - Instance Type: Free
# 5. Create Web Service

# Step 3: Set up auto-ping (keep awake)
# Go to: https://cron-job.org
# 1. Create account
# 2. New Cron Job
# 3. URL: https://trading-api-xxx.onrender.com/health
# 4. Schedule: */10 * * * * (every 10 minutes)
# 5. Save

# Done! Your API is now 24/7 available FOR FREE! 🎉
```

---

## ⚠️ Important Notes

1. **Render.com requires GitHub** - Push your code first
2. **Cron job prevents sleeping** - Set it up immediately after deploy
3. **First request after deploy** - May take 30s (building)
4. **Paper trading during market hours only** - But API available 24/7 for testing
5. **Monitor logs** - Render dashboard shows all requests

---

## 📞 Next Steps

1. **Choose platform** - Render.com recommended for FREE 24/7
2. **Deploy** - Follow quick start above
3. **Set up cron** - Keep API awake
4. **Test 24/7** - Your API will always respond
5. **Paper trade** - Collect predictions during market hours (9:30-4:00 EST)
6. **Validate** - Compare predictions vs actual prices for 3-6 months

---

**🎯 Bottom Line:**

- **Best FREE 24/7 option**: Render.com + cron-job.org
- **Best paid option**: Railway.app ($5/month)
- **For your use case**: Render is perfect for 3-6 month paper trading validation!

Would you like me to guide you through deploying to Render.com right now? 🚀
