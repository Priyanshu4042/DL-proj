# Railway.app Deployment Instructions
# ==========================================
# EASIEST DEPLOYMENT METHOD (5 minutes)

## What is Railway.app?
# - Modern cloud platform
# - One-click deployment from GitHub
# - Auto-detects Python/Docker projects
# - HTTPS included
# - $5/month with free trial

## Step-by-Step Deployment:

### 1. PUSH YOUR CODE TO GITHUB (if not already done)
# 
# In your terminal:
git init
git add .
git commit -m "Trading model with advanced LSTM ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/FinBERT-LSTM.git
git push -u origin main

### 2. GO TO RAILWAY.APP
# 
# Open browser: https://railway.app
# Click "Start a New Project"
# Login with GitHub

### 3. DEPLOY FROM GITHUB
# 
# 1. Click "Deploy from GitHub repo"
# 2. Select "FinBERT-LSTM" repository
# 3. Railway auto-detects Dockerfile in /api folder
# 4. Click "Deploy"
# 
# That's it! Railway will:
# - Build your Docker image
# - Deploy to cloud
# - Assign public URL
# - Set up HTTPS

### 4. CONFIGURE (Optional)
# 
# In Railway dashboard:
# - Click your deployment
# - Go to "Settings"
# - Add environment variables (if needed):
#   - LOG_LEVEL=info
#   - API_KEY=your-secret-key (for auth)
# 
# Go to "Networking"
# - Your public URL will be shown: https://your-app.railway.app

### 5. TEST YOUR DEPLOYMENT
# 
# Open browser:
# https://your-app.railway.app/docs  (API documentation)
# https://your-app.railway.app/health (health check)

### 6. MAKE API CALLS
# 
# In Python:
import requests

response = requests.post('https://your-app.railway.app/predict', json={
    "price_history": [12000, 12050, 12100, 12080, 12120, 12150, 12200, 12180, 12220, 12250],
    "sentiment_history": [0.2, 0.1, -0.1, 0.3, 0.4, 0.2, 0.5, 0.3, 0.6, 0.4]
})

print(response.json())

## DONE! Your trading model is now live! 🎉

## Monitoring:
# Railway dashboard shows:
# - Request logs
# - Error logs
# - CPU/Memory usage
# - Deployment status

## Costs:
# - Free tier: $5 credit/month
# - Hobby plan: $5/month
# - Pro plan: $20/month (if you need more resources)

## Advantages:
# ✅ Automatic HTTPS
# ✅ Auto-scaling
# ✅ Git-based deployment (push to deploy)
# ✅ Built-in monitoring
# ✅ Easy rollback to previous versions
# ✅ Environment variables management
# ✅ Custom domains supported

## Need Help?
# Railway docs: https://docs.railway.app
# Discord: https://discord.gg/railway
