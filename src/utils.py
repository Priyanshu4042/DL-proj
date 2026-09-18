



import yfinance as yf
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from datetime import datetime, timedelta
import json
import os
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ===================================================================
# CONFIGURATION - BACKTESTING FOCUSED
# ===================================================================
# Configuration
ALPACA_API_KEY = "PKQLLHPOS3CAB0HNXJ6B"
ALPACA_SECRET_KEY = "4avolaORY3POxhvor3SCkq0frCsB7DMOo12iJc1W"
PAPER_TRADING_URL = "https://app.alpaca.markets/paper/"

# Backtesting Parameters
SYMBOLS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA']
START_DATE = "2020-01-01"  # 3 years of data for robust backtesting
END_DATE = "2025-10-1" 
TRAIN_MONTHS = 25     # 6 months training window
VAL_MONTHS = 5       # 1 month validation window  
TEST_MONTHS = 3      # 1 month test window

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Initialize clients
news_client = NewsClient(api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY)

# FinBERT setup
print("🧠 Loading FinBERT...")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)

# ===================================================================
# DATA MANAGEMENT CLASS - SIMPLIFIED
# ===================================================================
class BacktestDataManager:
    def __init__(self):
        self.setup_directories()
        self.scalers = {}  # Store scalers for each symbol
        
    def setup_directories(self):
        os.makedirs("data/price_data", exist_ok=True)
        os.makedirs("data/news_data", exist_ok=True)
        os.makedirs("data/models", exist_ok=True)
        
    def save_json(self, data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_json(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    
    def get_sentiment_features(self, news_texts):
        """FinBERT sentiment analysis"""
        if not news_texts or all(not text for text in news_texts):
            return torch.tensor([0.33, 0.33, 0.34, 0.0, 0.33])
        
        combined_text = " ".join([text for text in news_texts if text])[:2000]
        tokens = tokenizer(combined_text, return_tensors="pt", padding=True, 
                          truncation=True, max_length=512).to(device)
        
        with torch.no_grad():
            result = finbert_model(tokens["input_ids"], attention_mask=tokens["attention_mask"])["logits"]
            probabilities = torch.nn.functional.softmax(result, dim=-1)
            
            pos_prob = probabilities[0][0].item()
            neg_prob = probabilities[0][1].item()  
            neu_prob = probabilities[0][2].item()
            
            sentiment_score = pos_prob - neg_prob
            confidence = max(pos_prob, neg_prob, neu_prob)
            
        return torch.tensor([pos_prob, neg_prob, neu_prob, sentiment_score, confidence])
    
    def collect_all_data(self):
        """Collect price and news data for all symbols"""
        start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
        end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
        
        print(f"📅 Collecting data: {START_DATE} to {END_DATE}")
        print(f"📊 Symbols: {SYMBOLS}")
        
        for symbol in SYMBOLS:
            print(f"\n🔄 Processing {symbol}...")
            self._collect_price_data(symbol, start_date, end_date)
            self._collect_news_data(symbol, start_date, end_date)
    
    def _collect_price_data(self, symbol, start_date, end_date):
        """Collect price data from yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return
            
            price_data = {
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'records': []
            }
            
            for date, row in df.iterrows():
                price_data['records'].append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            filepath = f"data/price_data/{symbol}_price.json"
            self.save_json(price_data, filepath)
            print(f"  📈 Price: {len(price_data['records'])} records")
            
        except Exception as e:
            print(f"  ❌ Price data error: {e}")
    
    def _collect_news_data(self, symbol, start_date, end_date):
        """Collect news data from Alpaca with proper pagination using page_token"""
        try:
            # Ensure dates are timezone-aware (UTC) to match Alpaca API response
            if start_date.tzinfo is None:
                from datetime import timezone
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                from datetime import timezone
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            news_data = {
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'records': []
            }

            # Alpaca News API pagination using page_token
            # NOTE: Free tier may limit total results to ~50 articles
            page_limit = 50  # Alpaca's limit per request
            page_token = None
            total_articles = 0
            iteration = 0
            max_iterations = 100  # Safety limit to prevent infinite loops
            
            print(f"  📰 Fetching news from {start_date.date()} to {end_date.date()}...")
            
            while iteration < max_iterations:
                iteration += 1
                try:
                    news_request = NewsRequest(
                        symbols=symbol, 
                        start=start_date, 
                        end=end_date, 
                        limit=page_limit,
                        page_token=page_token
                    )
                    news_response = news_client.get_news(news_request)

                    # Extract articles from response.data['news']
                    all_articles = []
                    if hasattr(news_response, 'data') and news_response.data:
                        if 'news' in news_response.data:
                            all_articles = news_response.data['news']
                    
                    # If no articles found, we've reached the end
                    if not all_articles:
                        if iteration == 1:
                            print(f"    ⚠️ No news articles found for {symbol} in this period")
                        break

                    # Process each article
                    for i, article in enumerate(all_articles):
                        try:
                            text = f"{article.headline} {getattr(article, 'summary', '') or ''}"
                            sentiment = self.get_sentiment_features([text])
                            news_data['records'].append({
                                'date': article.created_at.strftime('%Y-%m-%d'),
                                'headline': article.headline,
                                'summary': getattr(article, 'summary', '') or '',
                                'sentiment_pos': float(sentiment[0]),
                                'sentiment_neg': float(sentiment[1]),
                                'sentiment_neu': float(sentiment[2]),
                                'sentiment_score': float(sentiment[3]),
                                'confidence': float(sentiment[4])
                            })
                        except Exception as article_error:
                            print(f"    ⚠️ Skipping article {i+1}: {article_error}")
                            continue

                    total_articles += len(all_articles)
                    print(f"    Page {iteration}: {len(all_articles)} articles (total: {total_articles})")

                    # Check for next page using page_token
                    page_token = news_response.next_page_token if hasattr(news_response, 'next_page_token') else None
                    
                    if not page_token:
                        if iteration == 1 and total_articles == page_limit:
                            print(f"    ℹ️ Note: Alpaca API may limit results. Got exactly {page_limit} articles.")
                        break
                        
                except Exception as fetch_error:
                    print(f"    ⚠️ Error fetching page {iteration}: {fetch_error}")
                    break

            filepath = f"data/news_data/{symbol}_news.json"
            self.save_json(news_data, filepath)
            print(f"  📰 News: {len(news_data['records'])} articles saved")

        except Exception as e:
            print(f"  ❌ News data error: {e}")
            import traceback
            traceback.print_exc()
            news_data = {'symbol': symbol, 'records': []}
            filepath = f"data/news_data/{symbol}_news.json"
            self.save_json(news_data, filepath)

# ===================================================================
# FINBERT-LSTM MODEL - SIMPLIFIED
# ===================================================================
class FinBERTLSTM(nn.Module):
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, dropout=0.2):
        super(FinBERTLSTM, self).__init__()
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        output = self.fc(self.dropout(last_output))
        return output

# ===================================================================
# WALK-FORWARD BACKTESTER - NO DATA LEAKAGE
# ===================================================================
class WalkForwardBacktester:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.results = []
        
    def prepare_data_for_period(self, symbol, start_date, end_date):
        """Prepare data for specific time period - NO FUTURE DATA"""
        # Load price data
        price_file = f"data/price_data/{symbol}_price.json"
        price_data = self.data_manager.load_json(price_file)
        
        # Load news data
        news_file = f"data/news_data/{symbol}_news.json"  
        news_data = self.data_manager.load_json(news_file)
        
        if not price_data.get('records'):
            return None, None
        
        # Convert to DataFrames
        price_df = pd.DataFrame(price_data['records'])
        price_df['date'] = pd.to_datetime(price_df['date'])
        
        # Filter date range - STRICT TEMPORAL ORDERING
        price_df = price_df[
            (price_df['date'] >= start_date) & 
            (price_df['date'] <= end_date)
        ].sort_values('date')  # ENSURE CHRONOLOGICAL ORDER
        
        if news_data.get('records'):
            news_df = pd.DataFrame(news_data['records'])
            news_df['date'] = pd.to_datetime(news_df['date'])
            
            # Filter and aggregate news by date
            news_df = news_df[
                (news_df['date'] >= start_date) & 
                (news_df['date'] <= end_date)
            ].sort_values('date')
            
            # Aggregate multiple news per day
            news_agg = news_df.groupby('date').agg({
                'sentiment_pos': 'mean',
                'sentiment_neg': 'mean', 
                'sentiment_neu': 'mean',
                'sentiment_score': 'mean',
                'confidence': 'mean'
            }).reset_index()
            
            # Merge with price data
            combined_df = pd.merge(price_df, news_agg, on='date', how='left')
        else:
            combined_df = price_df.copy()
            # Add neutral sentiment for missing news
            for col in ['sentiment_pos', 'sentiment_neg', 'sentiment_neu', 'sentiment_score', 'confidence']:
                combined_df[col] = 0.33
        
        # Fill missing sentiment values
        sentiment_cols = ['sentiment_pos', 'sentiment_neg', 'sentiment_neu', 'sentiment_score', 'confidence']
        combined_df[sentiment_cols] = combined_df[sentiment_cols].fillna(0.33)
        
        # Create features and targets
        feature_cols = ['open', 'high', 'low', 'close', 'volume'] + sentiment_cols
        
        X = combined_df[feature_cols].values
        y = combined_df['close'].shift(-1).values  # Next day's close price
        
        # Remove last row (no future target)
        X = X[:-1]
        y = y[:-1]
        
        return X, y, combined_df[:-1]
    
    def create_sequences(self, X, y, sequence_length=10):
        """Create LSTM sequences - TEMPORAL ORDER PRESERVED"""
        sequences_X, sequences_y = [], []
        
        if len(X) <= sequence_length:
            return np.array([]), np.array([])
        
        for i in range(sequence_length, len(X)):
            # Use past 10 days to predict next day - NO FUTURE DATA
            sequences_X.append(X[i-sequence_length:i])
            sequences_y.append(y[i])
        
        return np.array(sequences_X), np.array(sequences_y)
    
    def run_walk_forward_backtest(self, symbol):
        """Run walk-forward analysis preventing data leakage"""
        print(f"\n🔄 Walk-Forward Backtesting: {symbol}")
        
        try:
            start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
            end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
            
            # Calculate total months
            total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            window_size = TRAIN_MONTHS + VAL_MONTHS + TEST_MONTHS
            
            print(f"  Total months available: {total_months}")
            print(f"  Window size needed: {window_size}")
            print(f"  Possible periods: {total_months - window_size + 1}")
            
            results = []
            
        except Exception as init_error:
            print(f"  ❌ Initialization error: {init_error}")
            return []
        
        for i in range(0, total_months - window_size + 1, TEST_MONTHS):  # Move forward by test period
            
            # Calculate period dates
            period_start = start_date + timedelta(days=30*i)
            train_end = period_start + timedelta(days=30*TRAIN_MONTHS) 
            val_end = train_end + timedelta(days=30*VAL_MONTHS)
            test_end = val_end + timedelta(days=30*TEST_MONTHS)
            
            print(f"\n📅 Period {i//TEST_MONTHS + 1}:")
            print(f"  Train: {period_start.strftime('%Y-%m-%d')} to {train_end.strftime('%Y-%m-%d')}")
            print(f"  Val:   {train_end.strftime('%Y-%m-%d')} to {val_end.strftime('%Y-%m-%d')}")
            print(f"  Test:  {val_end.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
            
            # 1. TRAINING DATA (Past only)
            X_train, y_train, train_df = self.prepare_data_for_period(symbol, period_start, train_end)
            if X_train is None or len(X_train) < 50:
                print(f"    ⚠️ Insufficient training data: {len(X_train) if X_train is not None else 0} samples")
                continue
                
            # 2. VALIDATION DATA (After training period)
            X_val, y_val, val_df = self.prepare_data_for_period(symbol, train_end, val_end)
            if X_val is None or len(X_val) < 10:
                print(f"    ⚠️ Insufficient validation data: {len(X_val) if X_val is not None else 0} samples")
                continue
                
            # 3. TEST DATA (After validation period - NEVER SEEN BY MODEL)
            X_test, y_test, test_df = self.prepare_data_for_period(symbol, val_end, test_end)
            if X_test is None or len(X_test) < 10:
                print(f"    ⚠️ Insufficient test data: {len(X_test) if X_test is not None else 0} samples")
                continue
                
            print(f"    Data sizes - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
            
            # Normalize features (fit on training data only)
            scaler = MinMaxScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            X_test_scaled = scaler.transform(X_test)
            
            # Create sequences
            X_train_seq, y_train_seq = self.create_sequences(X_train_scaled, y_train)
            X_val_seq, y_val_seq = self.create_sequences(X_val_scaled, y_val) 
            X_test_seq, y_test_seq = self.create_sequences(X_test_scaled, y_test)
            
            print(f"    Sequences created - Train: {len(X_train_seq)}, Val: {len(X_val_seq)}, Test: {len(X_test_seq)}")
            
            if len(X_train_seq) < 10 or len(X_test_seq) < 5:
                print(f"    ⚠️ Insufficient data for sequences (Train: {len(X_train_seq)}, Test: {len(X_test_seq)})")
                continue
            
            try:
                # Train model
                model = FinBERTLSTM(input_size=X_train_seq.shape[-1])
                model = self._train_model(model, X_train_seq, y_train_seq, X_val_seq, y_val_seq)
                
                # Test on unseen data
                test_performance = self._evaluate_model(model, X_test_seq, y_test_seq, test_df)
                test_performance['period'] = i//TEST_MONTHS + 1
                test_performance['test_start'] = val_end.strftime('%Y-%m-%d')
                test_performance['test_end'] = test_end.strftime('%Y-%m-%d')
                
                results.append(test_performance)
                print(f"  📊 Test Return: {test_performance['total_return']:.2f}%")
                
            except Exception as model_error:
                print(f"    ❌ Model training/testing failed: {model_error}")
                continue
        
        return results
    
    def _train_model(self, model, X_train, y_train, X_val, y_val):
        """Train model with validation"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        
        # Convert to tensors
        X_train = torch.FloatTensor(X_train).to(device)
        y_train = torch.FloatTensor(y_train).to(device)
        X_val = torch.FloatTensor(X_val).to(device)
        y_val = torch.FloatTensor(y_val).to(device)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(50):  # Reduced epochs for faster testing
            model.train()
            optimizer.zero_grad()
            
            outputs = model(X_train)
            loss = criterion(outputs.squeeze(), y_train)
            loss.backward()
            optimizer.step()
            
            # Validation every 10 epochs to reduce output
            if epoch % 10 == 0:
                model.eval()
                with torch.no_grad():
                    val_outputs = model(X_val)
                    val_loss = criterion(val_outputs.squeeze(), y_val)
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    break
        
        return model
    
    def _evaluate_model(self, model, X_test, y_test, test_df):
        """Evaluate model performance using directional signals"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        X_test_tensor = torch.FloatTensor(X_test).to(device)
        
        model.eval()
        with torch.no_grad():
            predictions = model(X_test_tensor).squeeze().cpu().numpy()
        
        # Get the subset of test_df that corresponds to our predictions
        lookback = 10
        df_subset = test_df.iloc[lookback:].reset_index(drop=True)
        actual_prices = df_subset['close'].values
        
        # Ensure we have matching lengths
        min_len = min(len(predictions), len(actual_prices))
        predictions = predictions[:min_len]
        actual_prices = actual_prices[:min_len]
        
        if min_len < 2:
            return {'total_return': 0.0, 'final_value': 10000, 'num_predictions': 0, 'num_trades': 0}
        
        # Simple directional strategy: predict if price will go up or down
        portfolio_value = 10000
        position = 0  # 0 = cash, 1 = long position
        
        for i in range(min_len - 1):
            current_price = actual_prices[i]
            next_day_prediction = predictions[i]
            
            # Get actual next day price for buy/sell decisions
            next_day_actual = actual_prices[i + 1]
            
            # Create signal based on prediction vs current price
            # If prediction > current price, expect price to rise (buy signal)
            # If prediction < current price, expect price to fall (sell signal)
            predicted_return = (next_day_prediction - current_price) / current_price
            
            # More lenient thresholds for signal-based trading
            if predicted_return > 0.001 and position == 0:  # Buy signal (0.1% threshold)
                position = portfolio_value / current_price
                portfolio_value = 0
            elif predicted_return < -0.001 and position > 0:  # Sell signal
                portfolio_value = position * current_price  
                position = 0
        
        # Close any remaining position
        if position > 0:
            portfolio_value = position * actual_prices[-1]
        
        total_return = (portfolio_value - 10000) / 10000 * 100
        
        # Count number of trades
        num_trades = 0
        for i in range(min_len - 1):
            pred_ret = (predictions[i] - actual_prices[i]) / actual_prices[i]
            if abs(pred_ret) > 0.001:
                num_trades += 1
        
        return {
            'total_return': total_return,
            'final_value': portfolio_value,
            'num_predictions': min_len,
            'num_trades': num_trades
        }
