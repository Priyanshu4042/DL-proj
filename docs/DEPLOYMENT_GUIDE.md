# 🚀 DEPLOYMENT GUIDE - Trading Model API

Complete guide to deploying your ML trading model to production.

---

## 📋 Table of Contents

1. [Local Deployment](#1-local-deployment)
2. [Docker Deployment](#2-docker-deployment)
3. [Cloud Deployment Options](#3-cloud-deployment-options)
4. [Production Considerations](#4-production-considerations)
5. [Monitoring & Maintenance](#5-monitoring--maintenance)

---

## 1. Local Deployment

### Prerequisites
- Python 3.10+
- Trained models (`mlp_model.keras`, `advanced_model_final.keras`)
- `ensemble_config.json`
- `price_scaler.pkl`

### Step 1: Prepare Environment

```powershell
# Navigate to API directory
cd api

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Copy Model Files

```powershell
# Copy trained models to api directory
Copy-Item ..\mlp_model.keras .
Copy-Item ..\advanced_model_final.keras .
Copy-Item ..\ensemble_config.json .
Copy-Item ..\price_scaler.pkl .
```

### Step 3: Save Price Scaler

If you don't have `price_scaler.pkl`, create it:

```python
# In your project root
import pickle
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

# Load training data
stock_df = pd.read_csv('stock_price.csv')
train_size = int(len(stock_df) * 0.6)
train_prices = stock_df['Close'].values[:train_size]

# Fit and save scaler
scaler = MinMaxScaler()
scaler.fit(train_prices.reshape(-1, 1))

with open('price_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("✓ Scaler saved to price_scaler.pkl")
```

Then copy it:
```powershell
Copy-Item price_scaler.pkl api\
```

### Step 4: Run API Server

```powershell
# From api directory
python app.py
```

Server will start at: **http://localhost:8000**

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Step 5: Test API

```powershell
# In a new terminal
python test_client.py
```

---

## 2. Docker Deployment

### Prerequisites
- Docker Desktop installed
- Models and config files ready

### Step 1: Build Docker Image

```powershell
# From api directory
docker build -t trading-model-api:latest .
```

### Step 2: Run Container

```powershell
# Run on port 8000
docker run -d \
  --name trading-api \
  -p 8000:8000 \
  trading-model-api:latest

# Check logs
docker logs trading-api

# Check health
docker exec trading-api curl http://localhost:8000/health
```

### Step 3: Using Docker Compose (Recommended)

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

Docker Compose includes:
- Trading Model API (port 8000)
- Redis cache (port 6379)
- Health checks
- Auto-restart

### Step 4: Test Dockerized API

```powershell
python test_client.py
```

---

## 3. Cloud Deployment Options

### Option A: AWS (Amazon Web Services)

#### **Using AWS Elastic Beanstalk** (Easiest)

1. **Install EB CLI:**
   ```powershell
   pip install awsebcli
   ```

2. **Initialize EB:**
   ```powershell
   cd api
   eb init -p docker trading-model-api --region us-east-1
   ```

3. **Create environment:**
   ```powershell
   eb create production-env
   ```

4. **Deploy:**
   ```powershell
   eb deploy
   ```

5. **Open in browser:**
   ```powershell
   eb open
   ```

**Cost:** ~$20-50/month for t3.small instance

#### **Using AWS ECS/Fargate** (More control)

1. **Push image to ECR:**
   ```powershell
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Create repository
   aws ecr create-repository --repository-name trading-model-api

   # Tag and push
   docker tag trading-model-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-model-api:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/trading-model-api:latest
   ```

2. **Create ECS Task Definition** (via AWS Console)
   - Container: Your ECR image
   - Port: 8000
   - Memory: 2GB
   - CPU: 0.5 vCPU

3. **Create ECS Service**
   - Launch type: Fargate
   - Desired tasks: 1
   - Load balancer: Application LB

**Cost:** ~$30-60/month for Fargate

---

### Option B: Google Cloud Platform (GCP)

#### **Using Cloud Run** (Serverless - Best for variable traffic)

1. **Install gcloud CLI:**
   ```powershell
   # Download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Build and deploy:**
   ```powershell
   cd api
   
   # Build with Cloud Build
   gcloud builds submit --tag gcr.io/<project-id>/trading-model-api
   
   # Deploy to Cloud Run
   gcloud run deploy trading-model-api \
     --image gcr.io/<project-id>/trading-model-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 1
   ```

3. **Get URL:**
   ```powershell
   gcloud run services describe trading-model-api --region us-central1
   ```

**Cost:** Pay-per-request, ~$5-20/month for low traffic

---

### Option C: Microsoft Azure

#### **Using Azure Container Instances** (Simple)

1. **Login to Azure:**
   ```powershell
   az login
   ```

2. **Create resource group:**
   ```powershell
   az group create --name trading-model-rg --location eastus
   ```

3. **Create container registry:**
   ```powershell
   az acr create --resource-group trading-model-rg --name tradingmodelacr --sku Basic
   ```

4. **Push image:**
   ```powershell
   az acr login --name tradingmodelacr
   docker tag trading-model-api:latest tradingmodelacr.azurecr.io/trading-model-api:latest
   docker push tradingmodelacr.azurecr.io/trading-model-api:latest
   ```

5. **Deploy container:**
   ```powershell
   az container create \
     --resource-group trading-model-rg \
     --name trading-api \
     --image tradingmodelacr.azurecr.io/trading-model-api:latest \
     --cpu 1 --memory 2 \
     --registry-login-server tradingmodelacr.azurecr.io \
     --registry-username <username> \
     --registry-password <password> \
     --dns-name-label trading-model-api \
     --ports 8000
   ```

**Cost:** ~$30-50/month

---

### Option D: Heroku (Easiest but expensive)

1. **Install Heroku CLI:**
   ```powershell
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create app:**
   ```powershell
   cd api
   heroku login
   heroku create trading-model-api
   ```

3. **Deploy with container:**
   ```powershell
   heroku container:login
   heroku container:push web
   heroku container:release web
   ```

4. **Open app:**
   ```powershell
   heroku open
   ```

**Cost:** $7/month (Eco dyno) or $25/month (Basic)

---

### Option E: Railway.app (Modern, Simple)

1. **Visit:** https://railway.app
2. **Connect GitHub repo** or **Deploy from Docker**
3. **Set environment variables** (if needed)
4. **Deploy!**

**Cost:** $5/month for hobby plan, free tier available

---

## 4. Production Considerations

### Security

#### 1. Add API Authentication

Add to `app.py`:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # Verify token (use JWT, API keys, etc.)
    if token != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Protect endpoints
@app.post("/predict")
async def predict(request: PredictionRequest, token: str = Depends(verify_token)):
    # ... existing code
```

#### 2. Add Rate Limiting

```powershell
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("10/minute")  # 10 requests per minute
async def predict(request: Request, ...):
    # ... existing code
```

#### 3. HTTPS/SSL

For production, always use HTTPS:

- **Cloud platforms:** Usually automatic
- **Self-hosted:** Use Let's Encrypt + Nginx

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caching

Add Redis caching for repeated predictions:

```python
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.post("/predict")
async def predict(request: PredictionRequest):
    # Create cache key
    cache_key = hashlib.md5(
        json.dumps(request.dict(), sort_keys=True).encode()
    ).hexdigest()
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Generate prediction
    result = model_service.predict(...)
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
```

### Environment Variables

Create `.env` file:

```ini
API_KEY=your-secret-api-key
MODEL_PATH=/app/models
LOG_LEVEL=info
REDIS_HOST=localhost
REDIS_PORT=6379
```

Load in `app.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('API_KEY')
```

---

## 5. Monitoring & Maintenance

### Logging

Structured logging for production:

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log predictions
logger.info("Prediction generated", extra={
    "current_price": current_price,
    "predicted_price": predicted,
    "signal": signal,
    "user_id": user_id
})
```

### Metrics with Prometheus

Add metrics endpoint:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
prediction_counter = Counter('predictions_total', 'Total predictions')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')

@app.post("/predict")
async def predict(...):
    prediction_counter.inc()
    
    with prediction_latency.time():
        result = model_service.predict(...)
    
    return result

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

Enhanced health check:

```python
@app.get("/health")
async def health_check():
    # Check models
    models_ok = model_service.loaded
    
    # Check Redis (if using)
    try:
        redis_client.ping()
        redis_ok = True
    except:
        redis_ok = False
    
    # Overall status
    healthy = models_ok and redis_ok
    
    return {
        "status": "healthy" if healthy else "degraded",
        "models": "ok" if models_ok else "error",
        "cache": "ok" if redis_ok else "error",
        "timestamp": datetime.now().isoformat()
    }
```

### Auto-scaling

Configure based on CPU/memory:

**AWS:**
```yaml
# ECS Service auto-scaling
ScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    TargetTrackingScaling:
      TargetValue: 70.0  # CPU %
      PredefinedMetricType: ECSServiceAverageCPUUtilization
```

**GCP Cloud Run:** Auto-scales automatically!

**Kubernetes:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trading-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trading-api
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 📊 Cost Comparison

| Platform | Setup Difficulty | Monthly Cost | Auto-scaling | Best For |
|----------|-----------------|--------------|--------------|----------|
| **Local** | Easy | $0 | No | Development |
| **Railway.app** | Very Easy | $5-20 | Yes | Small projects |
| **Heroku** | Easy | $7-25 | Limited | Quick prototypes |
| **GCP Cloud Run** | Medium | $5-30 | Yes | Variable traffic |
| **AWS Elastic Beanstalk** | Medium | $20-50 | Yes | AWS ecosystem |
| **AWS ECS/Fargate** | Hard | $30-100 | Yes | Enterprise |
| **Azure Container Instances** | Medium | $30-50 | Limited | Azure ecosystem |
| **Self-hosted VPS** | Hard | $5-20 | No | Full control |

---

## 🎯 Recommended Deployment Path

### For Learning/Testing:
1. ✅ **Local deployment** (free, easy)
2. Test with `test_client.py`

### For Production (Small Scale):
1. ✅ **Docker locally** (ensure it works)
2. ✅ **Railway.app or GCP Cloud Run** (easiest cloud)
3. Add monitoring (Prometheus + Grafana)
4. Set up alerts

### For Production (Enterprise):
1. ✅ **Docker + Docker Compose**
2. ✅ **AWS ECS or Google Cloud Run**
3. Add load balancer
4. Implement CI/CD (GitHub Actions)
5. Set up monitoring (DataDog, New Relic)
6. Database for prediction logging
7. Auto-scaling policies

---

## 🔥 Quick Start (Fastest Path to Production)

```powershell
# 1. Prepare models
cd api
Copy-Item ..\mlp_model.keras .
Copy-Item ..\ensemble_config.json .
# ... copy other files

# 2. Test locally
python app.py

# 3. Test with client
python test_client.py

# 4. Deploy to Railway.app
# - Create account: https://railway.app
# - Connect GitHub repo
# - Deploy!

# OR deploy to GCP Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/trading-api
gcloud run deploy --image gcr.io/PROJECT_ID/trading-api
```

Done! 🎉

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Docker Docs:** https://docs.docker.com/
- **AWS ECS Guide:** https://docs.aws.amazon.com/ecs/
- **GCP Cloud Run:** https://cloud.google.com/run/docs
- **Monitoring Best Practices:** https://prometheus.io/docs/practices/

---

## 🆘 Troubleshooting

### API won't start
```powershell
# Check if models exist
ls mlp_model.keras
ls ensemble_config.json

# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list
```

### Docker build fails
```powershell
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t trading-model-api .
```

### Predictions are slow
- Add Redis caching
- Use smaller batch sizes
- Enable GPU (if available)
- Scale horizontally (multiple containers)

### Out of memory
- Increase container memory (2GB minimum)
- Use model quantization
- Implement batch processing

---

**Need help?** Open an issue or contact support!
