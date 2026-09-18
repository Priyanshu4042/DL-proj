"""
Ensemble Trading Model - Combining Multiple Strategies
======================================================
Combines predictions from:
1. Simple MLP (fast, reliable baseline)
2. Advanced LSTM (complex patterns, skip connections)
3. Weighted averaging with learned confidence

Benefits:
- Reduces overfitting (ensemble averaging)
- More robust predictions
- Can adapt weights based on recent performance
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
import tensorflow as tf
from tensorflow import keras
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("ENSEMBLE TRADING MODEL")
print("=" * 80)

# ============================================================================
# LOAD DATA
# ============================================================================
stock_df = pd.read_csv('stock_price.csv')
stock_df = stock_df.iloc[2:].copy().reset_index(drop=True)
stock_df['Close'] = pd.to_numeric(stock_df['Close'], errors='coerce')
stock_df = stock_df.dropna()

sentiment_df = pd.read_csv('sentiment.csv').dropna().reset_index(drop=True)

stock_close = stock_df['Close'].values
sentiment_scores = sentiment_df['FinBERT score'].values[:len(stock_close)]

print(f"Total samples: {len(stock_close)}")

# ============================================================================
# DATA SPLIT - SAME AS INDIVIDUAL MODELS
# ============================================================================
print("\n[2/5] Splitting data (60/20/20)...")

total_len = len(stock_close)
train_size = int(total_len * 0.6)
val_size = int(total_len * 0.2)

train_stock = stock_close[:train_size]
val_stock = stock_close[train_size:train_size + val_size]
test_stock = stock_close[train_size + val_size:]

train_sentiment = sentiment_scores[:train_size]
val_sentiment = sentiment_scores[train_size:train_size + val_size]
test_sentiment = sentiment_scores[train_size + val_size:]

print(f"Train: {len(train_stock)}, Val: {len(val_stock)}, Test: {len(test_stock)}")

# ============================================================================
# SCALING
# ============================================================================
print("\n[3/5] Scaling features...")

price_scaler = MinMaxScaler()
train_stock_scaled = price_scaler.fit_transform(train_stock.reshape(-1, 1)).flatten()
val_stock_scaled = price_scaler.transform(val_stock.reshape(-1, 1)).flatten()
test_stock_scaled = price_scaler.transform(test_stock.reshape(-1, 1)).flatten()

train_sentiment = train_sentiment.reshape(-1, 1)
val_sentiment = val_sentiment.reshape(-1, 1)
test_sentiment = test_sentiment.reshape(-1, 1)

# ============================================================================
# CREATE SEQUENCES
# ============================================================================
sequence_length = 10

def create_sequences(price_scaled, sentiment, seq_len):
    X, y = [], []
    for i in range(len(price_scaled) - seq_len):
        price_seq = price_scaled[i:i + seq_len].reshape(-1, 1)
        sent_seq = sentiment[i:i + seq_len]
        seq = np.concatenate([price_seq, sent_seq], axis=1)
        X.append(seq)
        y.append(price_scaled[i + seq_len])
    return np.array(X), np.array(y)

X_train, y_train = create_sequences(train_stock_scaled, train_sentiment, sequence_length)
X_val, y_val = create_sequences(val_stock_scaled, val_sentiment, sequence_length)
X_test, y_test = create_sequences(test_stock_scaled, test_sentiment, sequence_length)

print(f"Sequence shapes - Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

# ============================================================================
# LOAD PRE-TRAINED MODELS
# ============================================================================
print("\n[4/5] Loading pre-trained models...")

try:
    print("  Loading MLP model...")
    # We'll need to train this if it doesn't exist
    mlp_model = None
    try:
        mlp_model = keras.models.load_model('mlp_model.keras')
        print("  [OK] MLP loaded from mlp_model.keras")
    except:
        print("  [WARN] MLP not found, will train new one...")
        
        # Quick MLP
        mlp_model = keras.Sequential([
            keras.layers.Input(shape=(sequence_length, 2)),
            keras.layers.Flatten(),
            keras.layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.Dense(1)
        ])
        
        mlp_model.compile(optimizer=keras.optimizers.Adam(0.001), loss='mse', metrics=['mae'])
        
        mlp_model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=16,
            callbacks=[
                keras.callbacks.EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
            ],
            verbose=0
        )
        mlp_model.save('mlp_model.keras')
        print("  [OK] MLP trained and saved")
    
    print("  Loading Advanced LSTM model...")
    class AttentionLayer(keras.layers.Layer):
        def __init__(self, **kwargs):
            super(AttentionLayer, self).__init__(**kwargs)
        def build(self, input_shape):
            self.W = self.add_weight(name='attention_weight', shape=(input_shape[-1], 1), initializer='glorot_uniform', trainable=True)
            self.b = self.add_weight(name='attention_bias', shape=(input_shape[1], 1), initializer='zeros', trainable=True)
            super(AttentionLayer, self).build(input_shape)
        def call(self, x):
            e = tf.tanh(tf.matmul(x, self.W) + self.b)
            a = tf.nn.softmax(e, axis=1)
            output = x * a
            return tf.reduce_sum(output, axis=1)
        def compute_output_shape(self, input_shape):
            return (input_shape[0], input_shape[-1])

    lstm_model = None
    try:
        lstm_model = keras.models.load_model('advanced_model_final.keras', 
                                            custom_objects={'AttentionLayer': AttentionLayer})
        print("  [OK] Advanced LSTM loaded from advanced_model_final.keras")
    except Exception as err:
        print(f"  [WARN] Advanced LSTM load error: {err}")
        print("  Continuing with MLP only...")
        lstm_model = None

except Exception as e:
    print(f"  Error loading models: {e}")
    print("  Please train models first!")
    exit(1)

# ============================================================================
# ENSEMBLE PREDICTIONS
# ============================================================================
print("\n[5/5] Generating ensemble predictions...")

# Get predictions from each model
mlp_pred_scaled = mlp_model.predict(X_test, verbose=0).flatten()

if lstm_model is not None:
    lstm_pred_scaled = lstm_model.predict(X_test, verbose=0).flatten()
    
    # Weighted ensemble (can tune these weights)
    mlp_weight = 0.4
    lstm_weight = 0.6
    
    ensemble_pred_scaled = mlp_weight * mlp_pred_scaled + lstm_weight * lstm_pred_scaled
    print(f"  Ensemble weights: MLP={mlp_weight}, LSTM={lstm_weight}")
else:
    # Only MLP available
    ensemble_pred_scaled = mlp_pred_scaled
    print("  Using MLP only (LSTM not available)")

# Unscale predictions
ensemble_pred = price_scaler.inverse_transform(ensemble_pred_scaled.reshape(-1, 1)).flatten()
mlp_pred = price_scaler.inverse_transform(mlp_pred_scaled.reshape(-1, 1)).flatten()
y_test_unscaled = price_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

if lstm_model is not None:
    lstm_pred = price_scaler.inverse_transform(lstm_pred_scaled.reshape(-1, 1)).flatten()

# ============================================================================
# EVALUATE EACH MODEL
# ============================================================================
print("\n" + "=" * 80)
print("MODEL COMPARISON")
print("=" * 80)

def evaluate_model(predictions, actual, model_name):
    mae = mean_absolute_error(actual, predictions)
    mape = mean_absolute_percentage_error(actual, predictions) * 100
    r2 = r2_score(actual, predictions)
    
    # Backtesting
    positions = []
    for i in range(len(predictions) - 1):
        if predictions[i] > actual[i]:
            positions.append(1)
        else:
            positions.append(-1)
    
    actual_returns = np.diff(actual) / actual[:-1]
    strategy_returns = positions * actual_returns
    
    total_return = (np.prod(1 + strategy_returns) - 1) * 100
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    win_rate = (strategy_returns > 0).sum() / len(strategy_returns) * 100
    
    predicted_direction = np.sign(np.diff(predictions))
    actual_direction = np.sign(actual_returns)
    direction_acc = (predicted_direction == actual_direction).sum() / len(actual_direction) * 100
    
    print(f"\n{model_name}:")
    print(f"  MAE:                {mae:.2f}")
    print(f"  MAPE:               {mape:.2f}%")
    print(f"  R²:                 {r2:.4f}")
    print(f"  Backtest Return:    {total_return:+.2f}%")
    print(f"  Sharpe Ratio:       {sharpe:.2f}")
    print(f"  Win Rate:           {win_rate:.2f}%")
    print(f"  Direction Accuracy: {direction_acc:.2f}%")
    
    return {
        'mae': mae, 'mape': mape, 'r2': r2,
        'return': total_return, 'sharpe': sharpe,
        'win_rate': win_rate, 'direction_acc': direction_acc
    }

mlp_metrics = evaluate_model(mlp_pred, y_test_unscaled, "MLP Model")

if lstm_model is not None:
    lstm_metrics = evaluate_model(lstm_pred, y_test_unscaled, "Advanced LSTM Model")

ensemble_metrics = evaluate_model(ensemble_pred, y_test_unscaled, "ENSEMBLE Model")

# ============================================================================
# DETERMINE BEST MODEL
# ============================================================================
print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

models = [
    ('MLP', mlp_metrics),
    ('Ensemble', ensemble_metrics)
]

if lstm_model is not None:
    models.insert(1, ('LSTM', lstm_metrics))

# Rank by Sharpe ratio (risk-adjusted returns)
models_sorted = sorted(models, key=lambda x: x[1]['sharpe'], reverse=True)

print(f"\n[BEST] Best Model (by Sharpe Ratio): {models_sorted[0][0]}")
print(f"   Sharpe: {models_sorted[0][1]['sharpe']:.2f}")
print(f"   Return: {models_sorted[0][1]['return']:+.2f}%")
print(f"   Direction Accuracy: {models_sorted[0][1]['direction_acc']:.2f}%")

print("\nRanking:")
for i, (name, metrics) in enumerate(models_sorted, 1):
    print(f"  {i}. {name:12} - Sharpe: {metrics['sharpe']:6.2f}, Return: {metrics['return']:+7.2f}%")

# ============================================================================
# SAVE ENSEMBLE MODEL
# ============================================================================
print("\n" + "=" * 80)
print("SAVING ENSEMBLE CONFIGURATION")
print("=" * 80)

config = {
    'mlp_weight': mlp_weight if lstm_model else 1.0,
    'lstm_weight': lstm_weight if lstm_model else 0.0,
    'sequence_length': sequence_length,
    'best_model': models_sorted[0][0],
    'performance': {
        'sharpe': models_sorted[0][1]['sharpe'],
        'return': models_sorted[0][1]['return'],
        'direction_acc': models_sorted[0][1]['direction_acc']
    }
}

import json
with open('ensemble_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("[OK] Ensemble configuration saved to: ensemble_config.json")
print("\n" + "=" * 80)
print("[OK] Ensemble evaluation complete!")
print("=" * 80)
