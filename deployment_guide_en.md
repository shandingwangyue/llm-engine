# Deployment and Operations Guide

## 🚀 Quick Start

### 1. System Requirements
- **Python**: 3.8+
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **Storage**: Space required for model files + 10GB free space
- **Operating System**: Linux/Windows/macOS

### 2. Installation Steps

```bash
# Clone the project
git clone <repository-url>
cd llm-service-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download model files (example)
mkdir -p models
# Place GGUF or HF model files in the models directory
```

### 3. Configure Environment Variables

Create `.env` file:
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2

# Model Configuration
MODEL_DIR=./models
DEFAULT_MODEL=llama-2-7b-chat

# Performance Configuration
MAX_CACHE_SIZE=1000
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=20

# Monitoring Configuration
ENABLE_MONITORING=true
METRICS_PORT=9090
```

### 4. Start the Service

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📦 Docker Deployment

### 1. Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create models directory
RUN mkdir -p models

# Expose ports
EXPOSE 8000 9090

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  llm-service:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - MODEL_DIR=/app/models
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 12G

  # Optional: Redis Cache
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 3. Build and Run
```bash
# Build image
docker build -t llm-service .

# Run container
docker run -d \
  -p 8000:8000 \
  -p 9090:9090 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --name llm-service \
  llm-service

# Using docker-compose
docker-compose up -d
```

## 🔧 Performance Tuning

### 1. Memory Optimization Configuration
```python
# Use these parameters when loading models
model_params = {
    'n_ctx': 2048,           # Context length
    'n_gpu_layers': 0,       # GPU layers (if GPU available)
    'n_threads': 4,          # CPU threads
    'n_batch': 512,          # Batch size
    'use_mmap': True,        # Memory mapping
    'use_mlock': False       # Avoid memory locking
}
```

### 2. System Parameter Tuning
```bash
# Linux system optimization
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
echo 'vm.swappiness = 10' >> /etc/sysctl.conf
sysctl -p

# Increase file descriptor limits
echo '* soft nofile 65535' >> /etc/security/limits.conf
echo '* hard nofile 65535' >> /etc/security/limits.conf
```

### 3. Model Quantization Recommendations
```bash
# Using 4-bit quantization (recommended)
# Reduces memory usage by ~75%, performance loss ~10-15%

# Using 8-bit quantization
# Reduces memory usage by ~50%, performance loss ~5-10%
```

## 📊 Monitoring and Logging

### 1. Health Check
```bash
# Check service status
curl http://localhost:8000/api/v1/health

# Check metrics
curl http://localhost:8000/metrics
```

### 2. Logging Configuration
```python
# logging_config.py
import logging
from logging.config import dictConfig

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    }
}

dictConfig(log_config)
```

### 3. Key Monitoring Metrics
- **Memory Usage**: Keep below 80%
- **CPU Usage**: Monitor peak usage
- **Request Latency**: P95 < 5 seconds
- **Error Rate**: < 1%
- **Concurrent Connections**: Monitor active connections

## 🛡️ Security Configuration

### 1. API Authentication
```python
# Add API key authentication
API_KEYS = {"your-secret-key": "user1"}

async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### 2. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/generate")
@limiter.limit("10/minute")
async def generate_text(request: Request):
    # ...
```

### 3. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 Operations Scripts

### 1. Start Script
```bash
#!/bin/bash
# start.sh

# Set environment
export PYTHONPATH=.
export ENV=production

# Start service
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

### 2. Monitoring Script
```bash
#!/bin/bash
# monitor.sh

# Check service status
check_service() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$response" -eq 200 ]; then
        echo "Service is healthy"
    else
        echo "Service is down, restarting..."
        # Restart logic
    fi
}

# Monitoring loop
while true; do
    check_service
    sleep 30
done
```

### 3. Log Cleanup Script
```bash
#!/bin/bash
# cleanup_logs.sh

# Keep logs for the last 7 days
find ./logs -name "*.log" -mtime +7 -delete

# Compress old logs
find ./logs -name "*.log" -mtime +3 -exec gzip {} \;
```

## 📋 Troubleshooting

### Common Issues and Solutions
1. **Insufficient Memory**: Reduce concurrency or use quantized models
2. **Model Loading Failure**: Check model file path and format
3. **Performance Degradation**: Check system resource usage
4. **Connection Timeouts**: Adjust timeout settings or optimize network

### Emergency Recovery Steps
```bash
# 1. Stop service
pkill -f uvicorn

# 2. Clear memory
sync && echo 3 > /proc/sys/vm/drop_caches

# 3. Restart service
./start.sh
```

This deployment guide provides a complete deployment solution from development to production, including Docker deployment, performance tuning, monitoring, and operations.
