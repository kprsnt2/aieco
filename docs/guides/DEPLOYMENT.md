# Deployment Guide

> Deploy AIEco on any infrastructure

---

## Deployment Options

| Method | Best For | Time |
|--------|----------|------|
| [One-Click Deploy](#one-click-deploy) | Quick start | 5 min |
| [Manual Deploy](#manual-deploy) | Custom setup | 15 min |
| [Docker](#docker-deployment) | Containerized | 10 min |
| [Kubernetes](#kubernetes) | Production | 30 min |

---

## Hardware Requirements

### Minimum

| Component | Requirement |
|-----------|-------------|
| CPU | 8 cores |
| RAM | 32 GB |
| Storage | 500 GB SSD |
| GPU | 12 GB VRAM (RTX 3060+) |

### Recommended (Cloud)

| Component | 4x MI300X | 8x MI300X |
|-----------|-----------|-----------|
| VRAM | 768 GB | 1.5 TB |
| Context | 1M tokens | 2M tokens |
| Models | 1 (GLM-4.7) | 2 (GLM + MiniMax) |
| Cost | $7.96/hr | $15.92/hr |

---

## One-Click Deploy

The simplest way to get started:

```bash
git clone https://github.com/yourusername/aieco.git
cd aieco
python deploy.py
```

### Deploy Options

```bash
# Preview without deploying
python deploy.py --dry-run

# Force local/small model
python deploy.py --local

# Force cloud configuration
python deploy.py --cloud
```

### What Happens

1. **Hardware Detection** - Finds your GPU(s)
2. **Model Selection** - Chooses optimal model for hardware
3. **Dependency Install** - Installs vLLM, FastAPI, etc.
4. **Model Download** - Downloads from HuggingFace (~300-500GB)
5. **Server Start** - Starts model server on port 8000

---

## Manual Deploy

For more control over the deployment:

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Model Server

For 8x MI300X:
```bash
./model-server/multi-model-8x.sh
```

For 4x GPUs:
```bash
./model-server/max-context-coding.sh
```

### 3. Start Backend (Optional)

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. Start Frontend (Optional)

```bash
cd frontend/chat-app
npm install
npm run dev
```

---

## Docker Deployment

### Using Docker Compose

```bash
# Cloud deployment (8x GPU)
docker-compose -f docker/docker-compose.cloud.yml up -d

# Local deployment
docker-compose -f docker/docker-compose.local.yml up -d
```

### Building Images

```bash
# Build backend
docker build -t aieco-backend:latest ./backend

# Build with vLLM (requires GPU)
docker build -t aieco-vllm:latest ./model-server
```

### Docker Compose Configuration

```yaml
# docker/docker-compose.cloud.yml
version: '3.8'

services:
  vllm-glm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - HIP_VISIBLE_DEVICES=0,1,2,3
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: >
      --model THUDM/glm-4.7-358b-a16b-fp8
      --served-model-name glm-4.7
      --tensor-parallel-size 4
      --max-model-len 1048576
      --trust-remote-code
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd
              count: 4
              capabilities: [gpu]

  vllm-minimax:
    image: vllm/vllm-openai:latest
    ports:
      - "8001:8000"
    environment:
      - HIP_VISIBLE_DEVICES=4,5,6,7
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: >
      --model MiniMaxAI/MiniMax-M2.1
      --served-model-name minimax-m2.1
      --tensor-parallel-size 4
      --max-model-len 204800
      --trust-remote-code
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd
              count: 4
              capabilities: [gpu]

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - VLLM_BASE_URL=http://vllm-glm:8000/v1
      - DATABASE_ENABLED=false
      - REDIS_ENABLED=false
    depends_on:
      - vllm-glm
```

---

## Kubernetes

### Prerequisites

- Kubernetes cluster with GPU support
- NVIDIA/AMD GPU operator installed
- Helm 3.x

### Deploy with Helm

```bash
# Add AIEco Helm repo
helm repo add aieco https://charts.aieco.dev
helm repo update

# Install
helm install aieco aieco/aieco \
  --namespace aieco \
  --create-namespace \
  --set gpu.count=8 \
  --set gpu.type=amd-mi300x \
  --set model.primary=glm-4.7-358b
```

### Custom Values

```yaml
# values.yaml
replicaCount: 1

gpu:
  count: 8
  type: amd-mi300x  # or nvidia-a100

model:
  primary:
    name: glm-4.7
    huggingface: THUDM/glm-4.7-358b-a16b-fp8
    context: 1048576
    gpus: "0,1,2,3"
  secondary:
    name: minimax-m2.1
    huggingface: MiniMaxAI/MiniMax-M2.1
    context: 204800
    gpus: "4,5,6,7"

backend:
  enabled: true
  replicas: 2

ingress:
  enabled: true
  host: aieco.yourcompany.com
  tls: true

persistence:
  storageClass: fast-ssd
  size: 1Ti
```

### Apply

```bash
helm install aieco aieco/aieco -f values.yaml
```

---

## Cloud Provider Guides

### AWS

```bash
# Launch p5.48xlarge (8x H100)
aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type p5.48xlarge \
  --key-name your-key

# SSH and deploy
ssh ubuntu@<ip>
git clone https://github.com/yourusername/aieco.git
cd aieco && python deploy.py
```

### Google Cloud

```bash
# Create A3 instance (8x H100)
gcloud compute instances create aieco-server \
  --machine-type=a3-highgpu-8g \
  --zone=us-central1-c \
  --image-family=ubuntu-2204-lts \
  --boot-disk-size=1024GB
```

### SF Compute (AMD MI300X)

```bash
# SSH to your instance
ssh user@your-instance.sfcompute.com

# Clone and deploy
git clone https://github.com/yourusername/aieco.git
cd aieco && python deploy.py
```

### IndiaAI/AIKosh

1. Apply at [indiaai.gov.in](https://indiaai.gov.in)
2. Get allocated GPU time
3. SSH to instance
4. Deploy:
```bash
git clone https://github.com/yourusername/aieco.git
cd aieco && python deploy.py
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT tokens | `your-secret-key` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `VLLM_BASE_URL` | Model server URL | `http://localhost:8000/v1` |
| `DATABASE_ENABLED` | Enable PostgreSQL | `false` |
| `REDIS_ENABLED` | Enable Redis | `false` |
| `DATABASE_URL` | PostgreSQL connection | - |
| `REDIS_URL` | Redis connection | - |
| `HF_TOKEN` | HuggingFace token | - |

### Example .env

```bash
# backend/.env
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=your-super-secret-key-change-me

VLLM_BASE_URL=http://localhost:8000/v1
DEFAULT_MODEL=glm-4.7

DATABASE_ENABLED=false
REDIS_ENABLED=false
```

---

## Post-Deployment

### Health Check

```bash
# Model server
curl http://localhost:8000/health

# Backend
curl http://localhost:8080/health
```

### Run Tests

```bash
cd backend
pytest tests/
```

### Monitor Logs

```bash
# Model server logs
tail -f vllm_glm-4.7.log

# Backend logs
tail -f backend/logs/aieco.log
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
# Use load balancer
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

  vllm-1:
    # ... config
  
  vllm-2:
    # ... config
```

### Vertical Scaling (More GPUs)

```bash
# Edit deploy.py configs to use more GPUs
# 8x GPUs = 2 models
# 16x GPUs = 2 models with redundancy
```

---

## Security Checklist

Before production:

- [ ] Change `JWT_SECRET_KEY`
- [ ] Enable HTTPS (TLS)
- [ ] Configure firewall rules
- [ ] Set up API key rotation
- [ ] Enable audit logging
- [ ] Configure rate limits
- [ ] Set up monitoring

---

*Need help? See [Troubleshooting](../DOCUMENTATION.md#troubleshooting)*
