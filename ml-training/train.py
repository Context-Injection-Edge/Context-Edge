"""
Context Edge - ML Training Pipeline

This script trains PyTorch models on LDO datasets and converts them to TensorRT
for deployment on NVIDIA Jetson edge devices.

Usage:
    python train.py --data-path /data/ldos --output-dir /models
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.utils.tensorboard import SummaryWriter
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import psycopg2
import boto3


# ============================================================================
# Model Architecture
# ============================================================================

class ContextEdgeModel(nn.Module):
    """
    Neural network for predictive maintenance with context awareness.

    Input:
        - Sensor data: vibration_x, vibration_y, temperature, current
        - Context embeddings: product_id, recipe_id, asset_id

    Output:
        - Failure mode classification: [normal, bearing, belt, motor, other]
    """

    def __init__(
        self,
        sensor_dim: int = 4,
        embedding_dim: int = 16,
        num_products: int = 100,
        num_recipes: int = 50,
        num_assets: int = 200,
        num_classes: int = 5,
        hidden_dim: int = 128
    ):
        super().__init__()

        # Embeddings for context (Industrial RAG augmentation)
        self.product_embedding = nn.Embedding(num_products, embedding_dim)
        self.recipe_embedding = nn.Embedding(num_recipes, embedding_dim)
        self.asset_embedding = nn.Embedding(num_assets, embedding_dim)

        # Input dimension: sensor + 3 embeddings
        input_dim = sensor_dim + (3 * embedding_dim)

        # Feed-forward network
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.BatchNorm1d(hidden_dim),

            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.BatchNorm1d(hidden_dim // 2),

            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),

            nn.Linear(hidden_dim // 4, num_classes)
        )

    def forward(self, sensor_data, product_ids, recipe_ids, asset_ids):
        # Embed context IDs
        product_emb = self.product_embedding(product_ids)
        recipe_emb = self.recipe_embedding(recipe_ids)
        asset_emb = self.asset_embedding(asset_ids)

        # Concatenate sensor data with context embeddings
        x = torch.cat([sensor_data, product_emb, recipe_emb, asset_emb], dim=1)

        # Forward pass
        logits = self.network(x)
        return logits


# ============================================================================
# Dataset Loader
# ============================================================================

class LDODataset(Dataset):
    """PyTorch dataset for LDOs (Labeled Data Objects)"""

    def __init__(self, ldos: List[Dict], scaler: StandardScaler = None):
        self.ldos = ldos

        # Extract features
        self.sensor_data = []
        self.product_ids = []
        self.recipe_ids = []
        self.asset_ids = []
        self.labels = []

        for ldo in ldos:
            # Sensor features
            self.sensor_data.append([
                ldo['sensor_data']['vibration_x'],
                ldo['sensor_data']['vibration_y'],
                ldo['sensor_data']['temperature'],
                ldo['sensor_data']['current']
            ])

            # Context IDs
            self.product_ids.append(ldo['context']['product_id'])
            self.recipe_ids.append(ldo['context']['recipe_id'])
            self.asset_ids.append(ldo['context']['asset_id'])

            # Ground truth label
            self.labels.append(ldo['ground_truth_label_id'])

        # Normalize sensor data
        self.sensor_data = np.array(self.sensor_data, dtype=np.float32)
        if scaler is None:
            self.scaler = StandardScaler()
            self.sensor_data = self.scaler.fit_transform(self.sensor_data)
        else:
            self.scaler = scaler
            self.sensor_data = self.scaler.transform(self.sensor_data)

    def __len__(self):
        return len(self.ldos)

    def __getitem__(self, idx):
        return {
            'sensor_data': torch.tensor(self.sensor_data[idx], dtype=torch.float32),
            'product_id': torch.tensor(self.product_ids[idx], dtype=torch.long),
            'recipe_id': torch.tensor(self.recipe_ids[idx], dtype=torch.long),
            'asset_id': torch.tensor(self.asset_ids[idx], dtype=torch.long),
            'label': torch.tensor(self.labels[idx], dtype=torch.long)
        }


# ============================================================================
# Data Loading from Runtime Backend
# ============================================================================

def load_ldos_from_postgres(limit: int = 100000) -> List[Dict]:
    """
    Load LDO metadata from PostgreSQL (runtime backend)

    Returns list of LDO IDs to download from S3
    """
    print(f"📊 Loading LDO metadata from PostgreSQL...")

    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DB', 'contextedge'),
        user=os.getenv('POSTGRES_USER', 'contextedge'),
        password=os.getenv('POSTGRES_PASSWORD', 'changeme')
    )

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT ldo_id, s3_path, ground_truth_label_id
        FROM ldos
        WHERE validated = true
        ORDER BY created_at DESC
        LIMIT {limit}
    """)

    ldos = []
    for ldo_id, s3_path, label_id in cursor.fetchall():
        ldos.append({
            'ldo_id': ldo_id,
            's3_path': s3_path,
            'ground_truth_label_id': label_id
        })

    conn.close()
    print(f"✅ Found {len(ldos)} validated LDOs")
    return ldos


def download_ldos_from_s3(ldo_metadata: List[Dict], output_dir: Path) -> List[Dict]:
    """Download LDO JSON files from S3/MinIO"""
    print(f"📥 Downloading LDOs from S3...")

    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('S3_ENDPOINT', 'http://localhost:9000'),
        aws_access_key_id=os.getenv('S3_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('S3_SECRET_KEY', 'minioadmin')
    )

    bucket = os.getenv('S3_BUCKET', 'context-edge-ldos')
    ldos = []

    for i, meta in enumerate(ldo_metadata):
        if i % 1000 == 0:
            print(f"  Downloaded {i}/{len(ldo_metadata)}...")

        local_path = output_dir / f"{meta['ldo_id']}.json"

        try:
            s3.download_file(bucket, meta['s3_path'], str(local_path))

            with open(local_path, 'r') as f:
                ldo = json.load(f)
                ldo['ground_truth_label_id'] = meta['ground_truth_label_id']
                ldos.append(ldo)
        except Exception as e:
            print(f"⚠️  Failed to download {meta['ldo_id']}: {e}")

    print(f"✅ Downloaded {len(ldos)} LDOs")
    return ldos


# ============================================================================
# Training Loop
# ============================================================================

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 50,
    lr: float = 1e-4,
    device: str = 'cuda'
) -> nn.Module:
    """Train PyTorch model with validation"""

    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

    writer = SummaryWriter('runs/context_edge_training')

    best_val_acc = 0.0
    patience_counter = 0

    print(f"\n🚀 Starting training for {epochs} epochs...")
    print(f"   Device: {device}")
    print(f"   Training samples: {len(train_loader.dataset)}")
    print(f"   Validation samples: {len(val_loader.dataset)}\n")

    for epoch in range(epochs):
        # ===== Training =====
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch in train_loader:
            sensor_data = batch['sensor_data'].to(device)
            product_ids = batch['product_id'].to(device)
            recipe_ids = batch['recipe_id'].to(device)
            asset_ids = batch['asset_id'].to(device)
            labels = batch['label'].to(device)

            optimizer.zero_grad()
            outputs = model(sensor_data, product_ids, recipe_ids, asset_ids)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()

        train_acc = 100 * train_correct / train_total
        train_loss /= len(train_loader)

        # ===== Validation =====
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch in val_loader:
                sensor_data = batch['sensor_data'].to(device)
                product_ids = batch['product_id'].to(device)
                recipe_ids = batch['recipe_id'].to(device)
                asset_ids = batch['asset_id'].to(device)
                labels = batch['label'].to(device)

                outputs = model(sensor_data, product_ids, recipe_ids, asset_ids)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total
        val_loss /= len(val_loader)

        # ===== Logging =====
        print(f"Epoch {epoch+1}/{epochs}")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")

        writer.add_scalar('Loss/train', train_loss, epoch)
        writer.add_scalar('Loss/val', val_loss, epoch)
        writer.add_scalar('Accuracy/train', train_acc, epoch)
        writer.add_scalar('Accuracy/val', val_acc, epoch)

        # ===== Early Stopping =====
        scheduler.step(val_loss)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), 'best_model.pth')
            print(f"  ✅ New best model saved (val_acc: {val_acc:.2f}%)")
        else:
            patience_counter += 1
            if patience_counter >= 10:
                print(f"\n⏹️  Early stopping triggered")
                break

    writer.close()

    # Load best model
    model.load_state_dict(torch.load('best_model.pth'))
    print(f"\n✅ Training complete! Best validation accuracy: {best_val_acc:.2f}%")

    return model


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Train Context Edge ML model')
    parser.add_argument('--data-path', type=str, default='/data/ldos', help='Path to LDO data')
    parser.add_argument('--output-dir', type=str, default='/models', help='Output directory for models')
    parser.add_argument('--samples', type=int, default=100000, help='Number of samples to use')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    args = parser.parse_args()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n🔧 Context Edge ML Training Pipeline")
    print(f"   Device: {device}")
    print(f"   Samples: {args.samples}")
    print(f"   Epochs: {args.epochs}\n")

    # 1. Load LDO metadata from PostgreSQL
    ldo_metadata = load_ldos_from_postgres(limit=args.samples)

    # 2. Download LDO files from S3
    output_path = Path(args.data_path)
    output_path.mkdir(parents=True, exist_ok=True)
    ldos = download_ldos_from_s3(ldo_metadata, output_path)

    # 3. Split dataset
    train_ldos, val_ldos = train_test_split(ldos, test_size=0.2, random_state=42)
    print(f"📊 Train: {len(train_ldos)} | Val: {len(val_ldos)}")

    # 4. Create datasets
    train_dataset = LDODataset(train_ldos)
    val_dataset = LDODataset(val_ldos, scaler=train_dataset.scaler)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    # 5. Create model
    model = ContextEdgeModel()
    print(f"\n📐 Model architecture:")
    print(model)
    print(f"\n   Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 6. Train
    model = train_model(
        model, train_loader, val_loader,
        epochs=args.epochs, lr=args.lr, device=device
    )

    # 7. Save final model
    model_path = Path(args.output_dir) / 'model-v2.1.pth'
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"\n💾 Model saved to: {model_path}")

    print(f"\n✅ Training pipeline complete!")
    print(f"\nNext steps:")
    print(f"  1. Convert to TensorRT: python convert.py --model {model_path}")
    print(f"  2. Deploy to edge: kubectl apply -f k8s/model-deployment-v2.1.yaml")


if __name__ == '__main__':
    main()
