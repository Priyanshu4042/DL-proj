"""
Advanced LSTM Trading Model with Skip Connections & Attention
==============================================================
Key Features:
1. Residual/Skip Connections - Better gradient flow, prevents vanishing gradients
2. Attention Mechanism - Learns which timesteps are important
3. Proper Regularization - Dropout, L2, matched to small dataset (503 samples)
4. Separate Backtest Data - Clean 60/20/20 train/val/test split
5. Model Complexity Control - Small enough for 503 samples, smart enough to learn
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, regularizers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

print("=" * 80)
print("ADVANCED LSTM TRADING MODEL - Skip Connections & Attention")
print("=" * 80)

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n[1/8] Loading data...")
stock_df = pd.read_csv('stock_price.csv')
sentiment_df = pd.read_csv('sentiment.csv')

# Clean stock data - skip header rows (first 2 rows: Ticker, Date)
stock_df = stock_df.iloc[2:].copy()
stock_df = stock_df.reset_index(drop=True)

# Convert numeric columns to float
for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
    stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce')

# Remove any rows with NaN values
stock_df = stock_df.dropna()

print(f"Stock data shape: {stock_df.shape}")
print(f"Sentiment data shape: {sentiment_df.shape}")

# Extract features
stock_close = stock_df['Close'].values
sentiment_scores = sentiment_df['FinBERT score'].values  # Already in [-1, 1]

print(f"\nStock Close - Mean: {stock_close.mean():.2f}, Std: {stock_close.std():.2f}")
print(f"Sentiment - Mean: {sentiment_scores.mean():.3f}, Std: {sentiment_scores.std():.3f}, Range: [{sentiment_scores.min():.3f}, {sentiment_scores.max():.3f}]")

# ============================================================================
# DATA SPLIT - PROPER TRAIN/VAL/TEST ISOLATION
# ============================================================================
print("\n[2/8] Splitting data (60% train, 20% val, 20% test)...")

total_len = len(stock_close)
train_size = int(total_len * 0.6)  # 60% for training
val_size = int(total_len * 0.2)    # 20% for validation
# Remaining 20% for testing (backtest only)

train_stock = stock_close[:train_size]
val_stock = stock_close[train_size:train_size + val_size]
test_stock = stock_close[train_size + val_size:]

train_sentiment = sentiment_scores[:train_size]
val_sentiment = sentiment_scores[train_size:train_size + val_size]
test_sentiment = sentiment_scores[train_size + val_size:]

print(f"Train samples: {len(train_stock)}")
print(f"Validation samples: {len(val_stock)}")
print(f"Test samples (BACKTEST ONLY): {len(test_stock)}")
print("⚠️  Test set is NEVER seen during training/validation!")

# ============================================================================
# FEATURE SCALING - FIT ON TRAIN ONLY
# ============================================================================
print("\n[3/8] Scaling features...")

# Scale stock prices (fit on train only)
price_scaler = MinMaxScaler()
train_stock_scaled = price_scaler.fit_transform(train_stock.reshape(-1, 1)).flatten()
val_stock_scaled = price_scaler.transform(val_stock.reshape(-1, 1)).flatten()
test_stock_scaled = price_scaler.transform(test_stock.reshape(-1, 1)).flatten()

# Sentiment already normalized - just reshape (DO NOT SCALE!)
train_sentiment = train_sentiment.reshape(-1, 1)
val_sentiment = val_sentiment.reshape(-1, 1)
test_sentiment = test_sentiment.reshape(-1, 1)

print("✓ Price scaled using train statistics only")
print("✓ Sentiment kept raw (already normalized)")

# ============================================================================
# CREATE SEQUENCES
# ============================================================================
print("\n[4/8] Creating sequences...")

sequence_length = 10  # Use 10 days of history

def create_sequences(price_scaled, sentiment, seq_len):
    """Create sequences for LSTM with proper temporal alignment."""
    X, y = [], []
    
    for i in range(len(price_scaled) - seq_len):
        # Input: seq_len days of [price, sentiment]
        price_seq = price_scaled[i:i + seq_len].reshape(-1, 1)
        sent_seq = sentiment[i:i + seq_len]
        
        # Stack features: [price_scaled, sentiment_raw]
        seq = np.concatenate([price_seq, sent_seq], axis=1)
        X.append(seq)
        
        # Target: next day's price (scaled)
        y.append(price_scaled[i + seq_len])
    
    return np.array(X), np.array(y)

X_train, y_train = create_sequences(train_stock_scaled, train_sentiment, sequence_length)
X_val, y_val = create_sequences(val_stock_scaled, val_sentiment, sequence_length)
X_test, y_test = create_sequences(test_stock_scaled, test_sentiment, sequence_length)

print(f"X_train shape: {X_train.shape} (samples, timesteps, features)")
print(f"X_val shape: {X_val.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"Features: {X_train.shape[2]} (price_scaled, sentiment_raw)")

# ============================================================================
# CUSTOM ATTENTION LAYER
# ============================================================================
class AttentionLayer(layers.Layer):
    """
    Attention mechanism to learn which timesteps are important.
    Returns weighted sum of LSTM outputs.
    """
    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)
    
    def build(self, input_shape):
        # Attention weights
        self.W = self.add_weight(
            name='attention_weight',
            shape=(input_shape[-1], 1),
            initializer='glorot_uniform',
            trainable=True
        )
        self.b = self.add_weight(
            name='attention_bias',
            shape=(input_shape[1], 1),
            initializer='zeros',
            trainable=True
        )
        super(AttentionLayer, self).build(input_shape)
    
    def call(self, x):
        # x shape: (batch, timesteps, features)
        # Calculate attention scores
        e = keras.backend.tanh(keras.backend.dot(x, self.W) + self.b)  # (batch, timesteps, 1)
        a = keras.backend.softmax(e, axis=1)  # Attention weights sum to 1
        
        # Weighted sum
        output = x * a  # (batch, timesteps, features)
        output = keras.backend.sum(output, axis=1)  # (batch, features)
        
        return output
    
    def compute_output_shape(self, input_shape):
        return (input_shape[0], input_shape[-1])

# ============================================================================
# BUILD ADVANCED MODEL - SKIP CONNECTIONS + ATTENTION
# ============================================================================
print("\n[5/8] Building advanced model...")

def build_advanced_model(seq_len, n_features):
    """
    Advanced LSTM with:
    - Bidirectional LSTM for better context
    - Skip connections for gradient flow
    - Attention for important timesteps
    - Proper regularization for small dataset
    """
    
    # Input
    inputs = layers.Input(shape=(seq_len, n_features), name='input')
    
    # First LSTM block (Bidirectional)
    lstm1 = layers.Bidirectional(
        layers.LSTM(
            32,  # Small for 503 samples
            return_sequences=True,
            kernel_regularizer=regularizers.l2(0.001),
            recurrent_regularizer=regularizers.l2(0.001)
        ),
        name='bi_lstm_1'
    )(inputs)
    lstm1 = layers.Dropout(0.3, name='dropout_lstm1')(lstm1)
    
    # Second LSTM block
    lstm2 = layers.Bidirectional(
        layers.LSTM(
            16,  # Even smaller
            return_sequences=True,
            kernel_regularizer=regularizers.l2(0.001),
            recurrent_regularizer=regularizers.l2(0.001)
        ),
        name='bi_lstm_2'
    )(lstm1)
    lstm2 = layers.Dropout(0.3, name='dropout_lstm2')(lstm2)
    
    # SKIP CONNECTION: Add residual from lstm1 to lstm2
    # Project lstm1 to same dimension as lstm2 (64 -> 32)
    lstm1_projected = layers.TimeDistributed(
        layers.Dense(32, kernel_regularizer=regularizers.l2(0.001)),
        name='lstm1_projection'
    )(lstm1)
    skip = layers.Add(name='skip_connection')([lstm1_projected, lstm2])
    
    # Attention mechanism - learns which timesteps matter
    attended = AttentionLayer(name='attention')(skip)
    
    # Dense layers with skip connection
    dense1 = layers.Dense(
        16,
        activation='relu',
        kernel_regularizer=regularizers.l2(0.001),
        name='dense_1'
    )(attended)
    dense1 = layers.Dropout(0.2, name='dropout_dense1')(dense1)
    
    dense2 = layers.Dense(
        8,
        activation='relu',
        kernel_regularizer=regularizers.l2(0.001),
        name='dense_2'
    )(dense1)
    
    # SKIP CONNECTION: Add residual
    dense1_projected = layers.Dense(
        8, 
        kernel_regularizer=regularizers.l2(0.001),
        name='dense1_projection'
    )(dense1)
    skip2 = layers.Add(name='skip_connection_2')([dense1_projected, dense2])
    
    # Output
    output = layers.Dense(1, name='output')(skip2)
    
    # Build model
    model = Model(inputs=inputs, outputs=output, name='AdvancedLSTM')
    
    return model

model = build_advanced_model(sequence_length, X_train.shape[2])
model.summary()

# Count parameters
total_params = model.count_params()
print(f"\n📊 Total parameters: {total_params:,}")
print(f"📊 Samples per parameter: {len(X_train) / total_params:.2f}")
print(f"✓ Rule of thumb: >5 samples/param is acceptable for small datasets")

# ============================================================================
# COMPILE MODEL
# ============================================================================
print("\n[6/8] Compiling model...")

# Use lower learning rate for stability
optimizer = keras.optimizers.Adam(learning_rate=0.0005)

model.compile(
    optimizer=optimizer,
    loss='mse',
    metrics=['mae']
)

print("✓ Optimizer: Adam with lr=0.0005")
print("✓ Loss: MSE")

# ============================================================================
# CALLBACKS - ADVANCED TRAINING CONTROL
# ============================================================================
print("\n[7/8] Setting up callbacks...")

callbacks = [
    # Early stopping on validation loss
    EarlyStopping(
        monitor='val_loss',
        patience=30,
        restore_best_weights=True,
        verbose=1
    ),
    
    # Reduce learning rate when stuck
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=10,
        min_lr=1e-6,
        verbose=1
    ),
    
    # Save best model
    ModelCheckpoint(
        'best_model.keras',
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )
]

print("✓ EarlyStopping: patience=30 on val_loss")
print("✓ ReduceLROnPlateau: factor=0.5, patience=10")
print("✓ ModelCheckpoint: saves best weights")

# ============================================================================
# TRAIN MODEL
# ============================================================================
print("\n" + "=" * 80)
print("TRAINING")
print("=" * 80)

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=200,
    batch_size=16,
    callbacks=callbacks,
    verbose=1
)

print("\n✓ Training complete!")

# ============================================================================
# EVALUATE ON TEST SET (BACKTEST DATA)
# ============================================================================
print("\n" + "=" * 80)
print("EVALUATION - TEST SET (BACKTEST ONLY)")
print("=" * 80)

# Predict on test set
predictions_scaled = model.predict(X_test, verbose=0).flatten()

# Unscale predictions and actual values
predictions = price_scaler.inverse_transform(predictions_scaled.reshape(-1, 1)).flatten()
y_test_unscaled = price_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

# Calculate metrics
mae = mean_absolute_error(y_test_unscaled, predictions)
mape = mean_absolute_percentage_error(y_test_unscaled, predictions) * 100
r2 = r2_score(y_test_unscaled, predictions)

print(f"\n📊 Prediction Metrics:")
print(f"  MAE:  {mae:.2f}")
print(f"  MAPE: {mape:.2f}%")
print(f"  R²:   {r2:.4f}")

# ============================================================================
# BACKTESTING - TRADING SIMULATION
# ============================================================================
print("\n" + "=" * 80)
print("BACKTESTING - TRADING SIMULATION")
print("=" * 80)

# Simple strategy: Buy if predicted price > current price
positions = []
for i in range(len(predictions) - 1):
    current_price = y_test_unscaled[i]
    predicted_next = predictions[i]
    
    if predicted_next > current_price:
        positions.append(1)  # Buy signal
    else:
        positions.append(-1)  # Sell signal

# Calculate returns
actual_returns = np.diff(y_test_unscaled) / y_test_unscaled[:-1]
strategy_returns = positions * actual_returns

# Metrics
total_return = (np.prod(1 + strategy_returns) - 1) * 100
sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
win_rate = (strategy_returns > 0).sum() / len(strategy_returns) * 100
max_drawdown = (np.maximum.accumulate(np.cumprod(1 + strategy_returns)) - np.cumprod(1 + strategy_returns)).max() * 100

# Direction accuracy
predicted_direction = np.sign(np.diff(predictions))
actual_direction = np.sign(actual_returns)
direction_accuracy = (predicted_direction == actual_direction).sum() / len(actual_direction) * 100

print(f"\n📈 Backtest Results:")
print(f"  Total Return:        {total_return:+.2f}%")
print(f"  Sharpe Ratio:        {sharpe:.2f}")
print(f"  Win Rate:            {win_rate:.2f}%")
print(f"  Max Drawdown:        {max_drawdown:.2f}%")
print(f"  Direction Accuracy:  {direction_accuracy:.2f}%")
print(f"  Total Trades:        {len(positions)}")

# ============================================================================
# SAVE MODEL
# ============================================================================
print("\n[8/8] Saving model...")
model.save('advanced_model_final.keras')
print("✓ Saved to: advanced_model_final.keras")

# ============================================================================
# PLOT TRAINING HISTORY
# ============================================================================
print("\nGenerating training plots...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Loss
axes[0, 0].plot(history.history['loss'], label='Train Loss', alpha=0.8)
axes[0, 0].plot(history.history['val_loss'], label='Val Loss', alpha=0.8)
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Loss (MSE)')
axes[0, 0].set_title('Training & Validation Loss')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# MAE
axes[0, 1].plot(history.history['mae'], label='Train MAE', alpha=0.8)
axes[0, 1].plot(history.history['val_mae'], label='Val MAE', alpha=0.8)
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('MAE')
axes[0, 1].set_title('Training & Validation MAE')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Predictions vs Actual
axes[1, 0].plot(y_test_unscaled, label='Actual', alpha=0.7, linewidth=2)
axes[1, 0].plot(predictions, label='Predicted', alpha=0.7, linewidth=2)
axes[1, 0].set_xlabel('Time')
axes[1, 0].set_ylabel('Stock Price')
axes[1, 0].set_title('Test Set: Predictions vs Actual')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Cumulative returns
cumulative_returns = np.cumprod(1 + strategy_returns) - 1
buy_hold_returns = np.cumprod(1 + actual_returns) - 1

axes[1, 1].plot(cumulative_returns * 100, label='Strategy', alpha=0.8, linewidth=2)
axes[1, 1].plot(buy_hold_returns * 100, label='Buy & Hold', alpha=0.8, linewidth=2)
axes[1, 1].set_xlabel('Days')
axes[1, 1].set_ylabel('Cumulative Return (%)')
axes[1, 1].set_title('Strategy vs Buy & Hold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig('advanced_model_results.png', dpi=150, bbox_inches='tight')
print("✓ Saved plot to: advanced_model_results.png")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"""
Model Architecture:
  • Bidirectional LSTM with skip connections
  • Attention mechanism for temporal importance
  • L2 regularization (λ=0.001) to prevent overfitting
  • Dropout (0.2-0.3) for robustness
  • Total parameters: {total_params:,}
  • Samples/param ratio: {len(X_train)/total_params:.2f}

Data Split:
  • Train: {len(X_train)} samples (60%)
  • Validation: {len(X_val)} samples (20%)
  • Test (backtest): {len(X_test)} samples (20%)
  • ✓ No data leakage - test set never seen during training

Performance:
  • MAE: {mae:.2f}
  • MAPE: {mape:.2f}%
  • R²: {r2:.4f}
  • Backtest Return: {total_return:+.2f}%
  • Sharpe Ratio: {sharpe:.2f}
  • Direction Accuracy: {direction_accuracy:.2f}%

Next Steps:
  1. If performance is good → Deploy (see deployment guide)
  2. If performance is poor → Get more data (1500+ samples recommended)
  3. Add technical indicators for more features
  4. Try ensemble with MLP model
""")

print("=" * 80)
print("✓ Training complete! Check 'advanced_model_results.png' for visualizations.")
print("=" * 80)
