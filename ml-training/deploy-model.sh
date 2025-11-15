#!/bin/bash
#
# Deploy Model Script - Simple deployment for 1-20 edge devices
# NO K3s required - just SSH and copy files
#
# Usage:
#   ./deploy-model.sh v2.1               # Deploy to all devices
#   ./deploy-model.sh v2.1 --pilot       # Deploy to pilot devices only
#   ./deploy-model.sh v2.1 --rollback    # Rollback to previous version
#

set -e  # Exit on error

MODEL_VERSION="${1:-}"
MODE="${2:---all}"

# Device configuration (edit this list!)
PILOT_DEVICES=(
  "edge-001"
  "edge-002"
  "edge-003"
  "edge-004"
  "edge-005"
)

ALL_DEVICES=(
  "edge-001"
  "edge-002"
  "edge-003"
  "edge-004"
  "edge-005"
  "edge-006"
  "edge-007"
  "edge-008"
  "edge-009"
  "edge-010"
  # Add more devices here...
)

# Edge device settings
EDGE_USER="nvidia"
MODEL_DIR="/opt/context-edge/models"
SERVICE_NAME="context-edge-inference"

# Model storage
MODEL_PATH="./models/model-${MODEL_VERSION}.trt"
S3_BUCKET="models"
S3_ENDPOINT="http://minio.factory.local:9000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

#================================
# Functions
#================================

print_usage() {
  cat << EOF
Usage: $0 <model_version> [--pilot|--all|--rollback]

Deploy AI models to edge devices (NO K3s required!)

Arguments:
  model_version   Model version to deploy (e.g., v2.1)

Options:
  --pilot        Deploy to pilot devices only (5 devices)
  --all          Deploy to all devices (default)
  --rollback     Rollback to previous model version

Examples:
  $0 v2.1                  # Deploy v2.1 to all devices
  $0 v2.1 --pilot          # Deploy v2.1 to pilot devices
  $0 v2.0 --rollback       # Rollback to v2.0

Device Configuration:
  Edit PILOT_DEVICES and ALL_DEVICES arrays at top of script
  Default SSH user: nvidia
  Default model directory: /opt/context-edge/models

EOF
  exit 1
}

download_model_from_s3() {
  echo -e "${YELLOW}📥 Downloading model ${MODEL_VERSION} from S3...${NC}"

  if command -v aws &> /dev/null; then
    aws s3 cp \
      --endpoint-url="${S3_ENDPOINT}" \
      "s3://${S3_BUCKET}/model-${MODEL_VERSION}.trt" \
      "${MODEL_PATH}"
  else
    echo -e "${RED}❌ AWS CLI not found. Please download model manually or install AWS CLI.${NC}"
    echo "   Manual download: aws s3 cp s3://${S3_BUCKET}/model-${MODEL_VERSION}.trt ${MODEL_PATH}"
    exit 1
  fi

  echo -e "${GREEN}✅ Model downloaded to ${MODEL_PATH}${NC}"
}

deploy_to_device() {
  local device=$1
  local host="${EDGE_USER}@${device}"

  echo -e "${YELLOW}📦 Deploying to ${device}...${NC}"

  # 1. Copy model file
  echo "   - Copying model file..."
  scp -q "${MODEL_PATH}" "${host}:/tmp/model-${MODEL_VERSION}.trt"

  # 2. Install and activate model
  echo "   - Installing model..."
  ssh -q "${host}" << EOF
    # Backup current model
    sudo cp ${MODEL_DIR}/current.trt ${MODEL_DIR}/current.trt.backup 2>/dev/null || true

    # Install new model
    sudo mv /tmp/model-${MODEL_VERSION}.trt ${MODEL_DIR}/model-${MODEL_VERSION}.trt
    sudo chmod 644 ${MODEL_DIR}/model-${MODEL_VERSION}.trt

    # Update symlink
    sudo rm -f ${MODEL_DIR}/current.trt
    sudo ln -s ${MODEL_DIR}/model-${MODEL_VERSION}.trt ${MODEL_DIR}/current.trt

    # Restart inference service
    echo "   - Restarting inference service..."
    sudo systemctl restart ${SERVICE_NAME}

    # Wait for service to start
    sleep 2

    # Check if service started successfully
    if systemctl is-active --quiet ${SERVICE_NAME}; then
      echo "   - Service restarted successfully"
      exit 0
    else
      echo "   - ERROR: Service failed to start, rolling back..."
      sudo rm -f ${MODEL_DIR}/current.trt
      sudo ln -s ${MODEL_DIR}/current.trt.backup ${MODEL_DIR}/current.trt
      sudo systemctl restart ${SERVICE_NAME}
      exit 1
    fi
EOF

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ ${device} deployed successfully${NC}"
    return 0
  else
    echo -e "${RED}❌ ${device} deployment FAILED${NC}"
    return 1
  fi
}

rollback_device() {
  local device=$1
  local host="${EDGE_USER}@${device}"

  echo -e "${YELLOW}⏪ Rolling back ${device}...${NC}"

  ssh -q "${host}" << EOF
    # Check if backup exists
    if [ ! -f ${MODEL_DIR}/current.trt.backup ]; then
      echo "   - ERROR: No backup found"
      exit 1
    fi

    # Rollback to backup
    sudo rm -f ${MODEL_DIR}/current.trt
    sudo ln -s ${MODEL_DIR}/current.trt.backup ${MODEL_DIR}/current.trt

    # Restart service
    sudo systemctl restart ${SERVICE_NAME}
    sleep 2

    if systemctl is-active --quiet ${SERVICE_NAME}; then
      echo "   - Rollback successful"
      exit 0
    else
      echo "   - ERROR: Rollback failed"
      exit 1
    fi
EOF

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ ${device} rolled back successfully${NC}"
    return 0
  else
    echo -e "${RED}❌ ${device} rollback FAILED${NC}"
    return 1
  fi
}

#================================
# Main
#================================

# Check arguments
if [ -z "$MODEL_VERSION" ]; then
  print_usage
fi

echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN} Context Edge - Model Deployment${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo " Model Version: ${MODEL_VERSION}"
echo " Mode: ${MODE}"
echo ""

# Select devices based on mode
if [ "$MODE" == "--pilot" ]; then
  DEVICES=("${PILOT_DEVICES[@]}")
  echo " Target: ${#DEVICES[@]} pilot devices"
elif [ "$MODE" == "--rollback" ]; then
  DEVICES=("${ALL_DEVICES[@]}")
  echo " Target: ${#DEVICES[@]} devices (ROLLBACK)"
else
  DEVICES=("${ALL_DEVICES[@]}")
  echo " Target: ${#DEVICES[@]} devices"
fi

echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment cancelled."
  exit 0
fi

# Download model from S3 (unless rollback)
if [ "$MODE" != "--rollback" ]; then
  if [ ! -f "${MODEL_PATH}" ]; then
    download_model_from_s3
  else
    echo -e "${GREEN}✅ Model ${MODEL_VERSION} already downloaded${NC}"
  fi
fi

# Deploy/rollback to all devices
SUCCESS=0
FAILED=0
FAILED_DEVICES=()

echo ""
echo -e "${YELLOW}Starting deployment...${NC}"
echo ""

for device in "${DEVICES[@]}"; do
  if [ "$MODE" == "--rollback" ]; then
    if rollback_device "$device"; then
      ((SUCCESS++))
    else
      ((FAILED++))
      FAILED_DEVICES+=("$device")
    fi
  else
    if deploy_to_device "$device"; then
      ((SUCCESS++))
    else
      ((FAILED++))
      FAILED_DEVICES+=("$device")
    fi
  fi
  echo ""
done

# Summary
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN} Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo " Success: ${SUCCESS}/${#DEVICES[@]} devices"
echo " Failed: ${FAILED}/${#DEVICES[@]} devices"
echo ""

if [ $FAILED -gt 0 ]; then
  echo -e "${RED}Failed devices:${NC}"
  for device in "${FAILED_DEVICES[@]}"; do
    echo "  - $device"
  done
  echo ""
  exit 1
else
  echo -e "${GREEN}✅ All devices deployed successfully!${NC}"
  echo ""
  exit 0
fi
