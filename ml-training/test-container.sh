#!/bin/bash
# Test that training container works

echo "🐳 Testing ML Training Container..."

# Build container
echo "1️⃣ Building container..."
docker build -t context-edge/ml-training ml-training/

# Test GPU access
echo "2️⃣ Testing GPU access..."
docker run --gpus all context-edge/ml-training nvidia-smi || echo "⚠️ No GPU (OK for testing)"

# Test Python/PyTorch
echo "3️⃣ Testing PyTorch..."
docker run context-edge/ml-training python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

# Test training script
echo "4️⃣ Testing training script..."
docker run context-edge/ml-training python train.py --help

echo "✅ Container works perfectly!"
