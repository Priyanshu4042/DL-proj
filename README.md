# 📈 FinBERT-LSTM: AI-Powered Quantitative Trading System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-PyTorch%20%7C%20TensorFlow-orange.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

Deep learning-based algorithmic stock trading system combining **NASDAQ historical prices** and **FinBERT financial news sentiment analysis** with **Residual Skip Connections**, **Temporal Attention Mechanisms**, and a **Real-Time Interactive Trading Dashboard**.

---

## 🚀 Key Features

- **Multi-Modal Architecture**: Merges time-series market data with NLP sentiment extracted from financial news.
- **Attention Mechanism & Skip Connections**: Overcomes vanishing gradients across longer sequences and dynamically weights high-impact news days.
- **Strict Out-of-Sample Validation**: Backtested with clean train/val/test splits (60/20/20) to eliminate data leakage and lookahead bias.
- **Interactive Web Trading Dashboard**: Live Chart.js visualization streaming real-time trades, portfolio equity curves, and BUY/SELL signals.
- **Production REST API**: Built on FastAPI with Docker and docker-compose deployment support.

---

## 📊 Model Performance Comparison

Evaluated on strictly unseen out-of-sample NASDAQ test data:

| Model Architecture | MAE | MAPE | R² Score | Backtest Return | Sharpe Ratio | Win Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MLP Baseline** | 383.08 | 3.15% | 0.5369 | +7.21% | 0.79 | 55.29% |
| **Advanced Attention-LSTM** | **353.81** | **2.93%** | **0.5754** | **+11.50%** | **1.15** | **55.29%** |
| **Ensemble (60% LSTM + 40% MLP)** | 364.78 | 3.02% | 0.5669 | **+11.50%** | **1.15** | **55.29%** |

---

## 📁 Project Structure

```text
finlstm-trading-bot/
├── api/                           # Production FastAPI server & Web Dashboard
│   ├── app.py                     # API endpoints & Chart.js live dashboard
│   ├── test_client.py             # Endpoint automated test script
│   ├── Dockerfile                 # Container image specification
│   └── docker-compose.yml         # Container orchestration
├── data/                          # Centralized Data Storage
│   ├── raw/                       # Original NASDAQ prices and news datasets
│   ├── processed/                 # Aligned sentiment-scored data (sentiment.csv)
│   └── cache/                     # Downloaded symbol caches (JSON)
├── docs/                          # Architecture reports and deployment guides
│   ├── ARCHITECTURE.md            # Deep learning model design details
│   ├── DEPLOYMENT_GUIDE.md        # Cloud & Docker production guides
│   └── DATA_COLLECTION_REPORT.md  # Alpaca API & news collection analysis
├── models/                        # Serialized model checkpoints & scalers
│   ├── advanced_model_final.keras # Trained Attention-LSTM weights
│   ├── mlp_model.keras            # Trained MLP baseline weights
│   ├── price_scaler.pkl           # Fitted price MinMaxScaler
│   └── ensemble_config.json       # Blending weights & performance metrics
├── notebooks/                     # Jupyter research notebooks
│   ├── 01_data_collection.ipynb   # Live data collection (Alpaca + yfinance)
│   └── 02_walk_forward_backtest.ipynb # Walk-forward sliding window backtest
├── results/                       # Generated evaluation plots & charts
│   ├── advanced_model_results.png # 4-quadrant training/test performance plot
│   └── model_evaluation.png       # PyTorch backtest visualization
├── src/                           # Source code & training pipelines
│   ├── data_cleaning.py           # News & price data alignment
│   ├── sentiment_analysis.py      # FinBERT scoring pipeline
│   ├── train_lstm.py              # Main Attention-LSTM training script
│   ├── evaluate_ensemble.py       # Multi-model comparative evaluation
│   ├── backtest_engine.py         # Strategy backtesting simulation
│   └── utils.py                   # PyTorch dataset & model utilities
├── .gitignore                     # Git ignore rules
├── README.md                      # Project documentation
└── requirements.txt               # Unified project dependencies
```

---

## ⚡ Quick Start

### 1. Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/<YOUR_USERNAME>/finlstm-trading-bot.git
cd finlstm-trading-bot

python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

---

### 2. Launch the Web Trading Dashboard

Start the FastAPI server:
```bash
cd api
python app.py
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**:
- Select your model (**Ensemble**, **Attention LSTM**, or **MLP**).
- Choose the data horizon (**86 Days Unseen Test Set** or **470 Days Full History**).
- Click **"Start Live Backtest"** to watch the simulated trading session animate in real-time!
- Interactive API documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

### 3. Model Training & Evaluation

To train the Attention-LSTM model from scratch:
```bash
python src/train_lstm.py
```

To run comparative evaluation across all models:
```bash
python src/evaluate_ensemble.py
```

---

### 4. Docker Deployment

To build and run the API container:
```bash
cd api
docker-compose up --build
```
The containerized service will be available at `http://localhost:8000`.

---

## 📄 License

This project is licensed under the MIT License.
