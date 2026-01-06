"""
Advanced Machine Learning Models for Institutional-Grade Trading
Includes LSTM, GRU, Transformers, and Ensemble Methods
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, List, Optional
import logging
from datetime import datetime
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """Custom PyTorch Dataset for time series data"""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMModel(nn.Module):
    """
    Advanced LSTM Network for Stock Price Prediction
    Architecture: Multi-layer LSTM with dropout and batch normalization
    """

    def __init__(self, input_size: int, hidden_size: int = 128,
                 num_layers: int = 3, dropout: float = 0.2,
                 output_size: int = 1):
        """
        Args:
            input_size: Number of input features
            hidden_size: Number of LSTM units per layer
            num_layers: Number of LSTM layers
            dropout: Dropout probability
            output_size: Number of output predictions
        """
        super(LSTMModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=False
        )

        # Batch normalization
        self.batch_norm = nn.BatchNorm1d(hidden_size)

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)

        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, batch_first=True)

    def forward(self, x):
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Take last timestep
        out = attn_out[:, -1, :]

        # Batch normalization
        out = self.batch_norm(out)

        # Fully connected layers
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class GRUModel(nn.Module):
    """
    Gated Recurrent Unit Model
    Lighter alternative to LSTM with similar performance
    """

    def __init__(self, input_size: int, hidden_size: int = 128,
                 num_layers: int = 2, dropout: float = 0.2,
                 output_size: int = 1):
        super(GRUModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )

        self.fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )

    def forward(self, x):
        out, h_n = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out


class TransformerModel(nn.Module):
    """
    Transformer-based Model for Time Series Prediction
    Uses positional encoding and multi-head self-attention
    """

    def __init__(self, input_size: int, d_model: int = 128,
                 nhead: int = 8, num_layers: int = 4,
                 dim_feedforward: int = 512, dropout: float = 0.1,
                 output_size: int = 1):
        """
        Args:
            input_size: Number of input features
            d_model: Dimension of the model
            nhead: Number of attention heads
            num_layers: Number of transformer encoder layers
            dim_feedforward: Dimension of feedforward network
            dropout: Dropout probability
            output_size: Number of output predictions
        """
        super(TransformerModel, self).__init__()

        self.d_model = d_model

        # Input embedding
        self.input_fc = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        # Transformer encoder
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layers, num_layers=num_layers
        )

        # Output layer
        self.fc_out = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size)
        )

    def forward(self, x):
        # Input embedding
        x = self.input_fc(x)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoding
        x = self.transformer_encoder(x)

        # Take mean across sequence
        x = torch.mean(x, dim=1)

        # Output layer
        out = self.fc_out(x)

        return out


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)

        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(1), 0, :]
        return self.dropout(x)


class AdvancedMLTrainer:
    """
    Trainer for advanced ML models with institutional-grade features
    """

    def __init__(self, model_type: str = 'lstm', device: str = None):
        """
        Args:
            model_type: 'lstm', 'gru', or 'transformer'
            device: 'cuda' or 'cpu' (auto-detected if None)
        """
        self.model_type = model_type
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.scaler = StandardScaler()
        self.history = {'train_loss': [], 'val_loss': []}

        logger.info(f"Using device: {self.device}")

    def create_sequences(self, data: np.ndarray, seq_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time series prediction

        Args:
            data: Input data (features)
            seq_length: Length of input sequences

        Returns:
            X: Input sequences, y: Target values
        """
        X, y = [], []

        for i in range(len(data) - seq_length):
            X.append(data[i:i + seq_length, :-1])  # All features except target
            y.append(data[i + seq_length, -1])  # Target (next day return)

        return np.array(X), np.array(y)

    def build_model(self, input_size: int, hidden_size: int = 128,
                   num_layers: int = 3, dropout: float = 0.2):
        """Build the specified model architecture"""

        if self.model_type == 'lstm':
            self.model = LSTMModel(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout
            )
        elif self.model_type == 'gru':
            self.model = GRUModel(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout
            )
        elif self.model_type == 'transformer':
            self.model = TransformerModel(
                input_size=input_size,
                d_model=hidden_size,
                nhead=8,
                num_layers=num_layers,
                dropout=dropout
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        self.model = self.model.to(self.device)
        logger.info(f"Built {self.model_type.upper()} model with {sum(p.numel() for p in self.model.parameters())} parameters")

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32,
              learning_rate: float = 0.001, patience: int = 10):
        """
        Train the model with early stopping

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data
            epochs: Maximum number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            patience: Early stopping patience
        """

        # Create data loaders
        train_dataset = TimeSeriesDataset(X_train, y_train)
        val_dataset = TimeSeriesDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                optimizer.step()
                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation phase
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)

                    outputs = self.model(batch_X).squeeze()
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()

            val_loss /= len(val_loader)

            # Update learning rate
            scheduler.step(val_loss)

            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_model.pth')
            else:
                patience_counter += 1

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch [{epoch+1}/{epochs}] - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

        # Load best model
        self.model.load_state_dict(torch.load('best_model.pth'))
        logger.info(f"Training completed. Best val loss: {best_val_loss:.6f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input sequences

        Returns:
            Predictions
        """
        self.model.eval()

        X_tensor = torch.FloatTensor(X).to(self.device)

        with torch.no_grad():
            predictions = self.model(X_tensor).cpu().numpy()

        return predictions.flatten()

    def save_model(self, filepath: str):
        """Save model to file"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'scaler': self.scaler,
            'history': self.history
        }, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str, input_size: int):
        """Load model from file"""
        checkpoint = torch.load(filepath, map_location=self.device)

        self.model_type = checkpoint['model_type']
        self.build_model(input_size)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.history = checkpoint['history']

        logger.info(f"Model loaded from {filepath}")


class EnsemblePredictor:
    """
    Ensemble multiple models for robust predictions
    Combines LSTM, GRU, and Transformer
    """

    def __init__(self, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.models = {}
        self.weights = {}

    def add_model(self, name: str, model: AdvancedMLTrainer, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models[name] = model
        self.weights[name] = weight
        logger.info(f"Added {name} to ensemble with weight {weight}")

    def predict(self, X: np.ndarray, method: str = 'weighted_average') -> np.ndarray:
        """
        Make ensemble predictions

        Args:
            X: Input data
            method: 'weighted_average', 'median', or 'voting'

        Returns:
            Ensemble predictions
        """
        predictions = {}

        for name, model in self.models.items():
            predictions[name] = model.predict(X)

        if method == 'weighted_average':
            total_weight = sum(self.weights.values())
            ensemble_pred = np.zeros_like(predictions[list(predictions.keys())[0]])

            for name, pred in predictions.items():
                ensemble_pred += pred * (self.weights[name] / total_weight)

            return ensemble_pred

        elif method == 'median':
            all_preds = np.array(list(predictions.values()))
            return np.median(all_preds, axis=0)

        elif method == 'voting':
            # For classification: majority vote
            all_preds = np.array(list(predictions.values()))
            return np.round(np.mean(all_preds > 0, axis=0))

        else:
            raise ValueError(f"Unknown ensemble method: {method}")


if __name__ == "__main__":
    # Example usage
    logger.info("Advanced ML Models Module - Institutional Grade")

    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    seq_length = 60

    # Simulate stock returns
    data = np.random.randn(n_samples, n_features)

    # Create trainer
    trainer = AdvancedMLTrainer(model_type='lstm')

    # Create sequences
    X, y = trainer.create_sequences(data, seq_length=seq_length)

    # Split data
    train_size = int(0.8 * len(X))
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]

    # Build and train model
    trainer.build_model(input_size=n_features - 1)
    trainer.train(X_train, y_train, X_val, y_val, epochs=50)

    # Make predictions
    predictions = trainer.predict(X_val[:10])
    print(f"Sample predictions: {predictions[:5]}")
