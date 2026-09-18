# 🏗️ Model Architecture Diagram

## Advanced LSTM Model with Skip Connections & Attention

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                              │
│         Shape: (batch_size, 10, 2)                          │
│         Features: [price_scaled, sentiment_raw]             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              BIDIRECTIONAL LSTM LAYER 1                     │
│   Units: 32 (16 forward + 16 backward)                      │
│   Output: 64 units total                                    │
│   Regularization: L2(0.001)                                 │
│   Return sequences: True                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├──────────┐ SKIP CONNECTION
                         │          │ (Project 64→32)
                         ▼          │
┌─────────────────────────────────────────────────────────────┐
│                   DROPOUT (0.3)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              BIDIRECTIONAL LSTM LAYER 2                     │
│   Units: 16 (8 forward + 8 backward)                        │
│   Output: 32 units total                                    │
│   Regularization: L2(0.001)                                 │
│   Return sequences: True                                    │
└────────────────────────┬────────────────────────────────────┘
                         │                     │
                         │◄────────────────────┘ ADD
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DROPOUT (0.3)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ATTENTION MECHANISM                            │
│                                                             │
│  Learns which timesteps are important:                      │
│  • Day 1: weight = 0.05                                     │
│  • Day 2: weight = 0.08                                     │
│  • ...                                                      │
│  • Day 10: weight = 0.25 (most recent)                      │
│                                                             │
│  Output: Weighted sum of LSTM states                        │
│          Shape: (batch_size, 32)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  DENSE LAYER 1                              │
│   Units: 16                                                 │
│   Activation: ReLU                                          │
│   Regularization: L2(0.001)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├──────────┐ SKIP CONNECTION
                         │          │ (Project 16→8)
                         ▼          │
┌─────────────────────────────────────────────────────────────┐
│                   DROPOUT (0.2)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  DENSE LAYER 2                              │
│   Units: 8                                                  │
│   Activation: ReLU                                          │
│   Regularization: L2(0.001)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │                     │
                         │◄────────────────────┘ ADD
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                              │
│   Units: 1 (predicted price - scaled)                      │
│   Activation: Linear                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components Explained

### 1. **Bidirectional LSTM**
```
Forward LSTM  →→→→→→→→→→
              Context
Backward LSTM ←←←←←←←←←←
```
- Captures patterns from both directions
- Better understanding of temporal dependencies
- Forward: learns from past to present
- Backward: learns from future to past (in training data)

### 2. **Skip/Residual Connections**
```
Input ─────────────┐
   │               │
   ▼               │
Layer 1            │
   │               │
   ▼               │
Layer 2            │
   │               │
   ├───────────────┘ ADD
   │
   ▼
Output
```

**Benefits:**
- Prevents vanishing gradients
- Allows training deeper networks
- Preserves information from earlier layers
- Helps optimization converge faster

### 3. **Attention Mechanism**
```
LSTM outputs at each timestep:
┌────┬────┬────┬─────┬─────┐
│ t1 │ t2 │ t3 │ ... │ t10 │
└────┴────┴────┴─────┴─────┘
  ↓    ↓    ↓     ↓     ↓
  α1   α2   α3   ...   α10  ← Learned weights (sum to 1)
  
Output = α1·t1 + α2·t2 + ... + α10·t10
```

**Benefits:**
- Learns which days are most important
- Recent days typically get higher weights
- Reduces impact of noisy historical data

### 4. **L2 Regularization**
```
Loss = MSE + λ·(∑weights²)
            ↑
      Penalty term (λ=0.001)
```

**Benefits:**
- Prevents overfitting on small dataset (503 samples)
- Encourages smaller weights
- Better generalization

### 5. **Dropout**
```
Training:
[1.2, 0.8, 1.5, 0.3] → [1.2, 0, 1.5, 0] (30% dropped)

Inference:
[1.2, 0.8, 1.5, 0.3] → [1.2, 0.8, 1.5, 0.3] (no dropout)
```

**Benefits:**
- Forces network to learn redundant representations
- Prevents co-adaptation of neurons
- Acts as ensemble of sub-networks

---

## Data Flow Example

### Input:
```python
price_history = [12000, 12050, 12100, ..., 12250]  # 10 days
sentiment = [0.2, 0.1, -0.1, ..., 0.4]             # 10 days

# After scaling
price_scaled = [0.15, 0.17, 0.19, ..., 0.28]
sentiment_raw = [0.2, 0.1, -0.1, ..., 0.4]  # NOT scaled!

# Combined input
X = [[0.15, 0.2],
     [0.17, 0.1],
     [0.19, -0.1],
     ...
     [0.28, 0.4]]  # Shape: (10, 2)
```

### Forward Pass:
```python
1. Bidirectional LSTM 1:
   Input:  (batch, 10, 2)
   Output: (batch, 10, 64)  # 32 units × 2 directions

2. Skip connection saves this output

3. Bidirectional LSTM 2:
   Input:  (batch, 10, 64)
   Output: (batch, 10, 32)  # 16 units × 2 directions

4. Add skip connection (after projection):
   Output: (batch, 10, 32)

5. Attention:
   Input:  (batch, 10, 32)
   Output: (batch, 32)  # Weighted sum over time

6. Dense layers with skip:
   32 → 16 → 8 → 1

7. Final output:
   Scaled prediction: 0.32
   Unscaled: 12380.45 (predicted price)
```

---

## Complexity Analysis

### Parameters:

| Layer | Parameters | Calculation |
|-------|-----------|-------------|
| BiLSTM 1 | 12,800 | 4 × ((2 + 64) × 32) × 2 |
| BiLSTM 2 | 8,256 | 4 × ((64 + 32) × 16) × 2 |
| Attention | 33 | 32 + 1 |
| Dense 1 | 528 | (32 + 1) × 16 |
| Skip 1 | 256 | 16 × 16 (projection) |
| Dense 2 | 136 | (16 + 1) × 8 |
| Skip 2 | 128 | 16 × 8 (projection) |
| Output | 9 | (8 + 1) × 1 |
| **Total** | **22,259** | |

### Samples per Parameter:
```
Training samples: 291
Parameters: 22,259
Ratio: 0.013 samples/param

⚠️ Generally want >10 samples/param
→ Need 222,590 samples for this model
→ Or reduce model size to ~2,910 params
```

**This is why we need more data!**

---

## Training Strategy

### 1. **Data Split** (60/20/20):
```
Total: 503 samples
├── Train: 301 → 291 sequences (60%)
├── Validation: 100 → 90 sequences (20%)
└── Test: 102 → 92 sequences (20%)
```

### 2. **Callbacks**:

**Early Stopping:**
```python
if val_loss doesn't improve for 30 epochs:
    stop training
    restore best weights
```

**Reduce LR on Plateau:**
```python
if val_loss doesn't improve for 10 epochs:
    learning_rate *= 0.5
    min_lr = 1e-6
```

**Model Checkpoint:**
```python
if val_loss < best_val_loss:
    save model to 'best_model.keras'
```

### 3. **Optimizer**:
```python
Adam(learning_rate=0.0005)
# Adaptive learning rates per parameter
# Momentum + RMSprop combined
```

---

## Comparison with Baseline Models

### MLP (Simple):
```
Input → Flatten → Dense(64) → Dense(32) → Dense(16) → Output
```
- **Pros:** Fast, simple, works well with small data
- **Cons:** No temporal structure, can't capture sequences

### LSTM (Basic):
```
Input → LSTM(64) → LSTM(32) → Dense(16) → Output
```
- **Pros:** Captures temporal patterns
- **Cons:** Vanishing gradients, no attention

### Advanced LSTM (This Model):
```
Input → BiLSTM(32) → BiLSTM(16) → Attention → Dense → Output
         ↓                 ↑                    ↓      ↑
         └─────Skip────────┘                    └──────┘
```
- **Pros:** Best of all worlds
- **Cons:** More complex, needs more data

---

## Ensemble Strategy

### Combining Models:
```python
# Predictions
mlp_pred = 12350.20
lstm_pred = 12400.10

# Weighted ensemble
ensemble = 0.4 × mlp_pred + 0.6 × lstm_pred
         = 0.4 × 12350.20 + 0.6 × 12400.10
         = 12380.45
```

**Why ensemble?**
- MLP good at: Simple patterns, stable predictions
- LSTM good at: Complex sequences, temporal dependencies
- Ensemble: Averages out weaknesses, more robust

---

## Visualization

### Training Progress:
```
Epoch 1-50: Learning basic patterns
  val_loss: 0.05 → 0.02 (improving fast)

Epoch 51-100: Fine-tuning
  val_loss: 0.02 → 0.015 (slower improvement)

Epoch 101-150: Convergence
  val_loss: 0.015 → 0.012 (plateau)

Epoch 151-200: Final tuning
  LR reduced: 0.0005 → 0.00025
  val_loss: 0.012 → 0.0112 (marginal gains)
```

### Attention Weights (Example):
```
Day  1: ▓░░░░░░░░░ 5%
Day  2: ▓▓░░░░░░░░ 7%
Day  3: ▓░░░░░░░░░ 6%
Day  4: ▓▓░░░░░░░░ 8%
Day  5: ▓▓▓░░░░░░░ 10%
Day  6: ▓▓▓░░░░░░░ 11%
Day  7: ▓▓▓▓░░░░░░ 12%
Day  8: ▓▓▓▓░░░░░░ 13%
Day  9: ▓▓▓▓▓░░░░░ 14%
Day 10: ▓▓▓▓▓▓░░░░ 16% ← Most recent!
```

---

## Future Improvements

1. **Transformer Architecture**
   - Replace LSTM with self-attention
   - Better parallelization
   - Capture longer dependencies

2. **Multi-Head Attention**
   - Learn multiple attention patterns
   - Price attention + sentiment attention separate

3. **Temporal Fusion**
   - Separate pathways for price and sentiment
   - Learn optimal fusion weights

4. **Graph Neural Networks**
   - Model correlations between stocks
   - Sector and market relationships

---

**Created:** November 4, 2025  
**Model Parameters:** 22,259  
**Training Time:** ~5-10 minutes (CPU)  
**Inference Time:** ~50ms per prediction
