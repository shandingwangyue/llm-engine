# 部署和运维指南

## 🚀 快速开始

### 1. 环境要求
- **Python**: 3.8+
- **内存**: 至少8GB RAM（推荐16GB+）
- **存储**: 模型文件所需空间 + 10GB可用空间
- **操作系统**: Linux/Windows/macOS

### 2. 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd llm-service-engine

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 下载模型文件（示例）
mkdir -p models
# 将GGUF或HF模型文件放入models目录
```

### 3. 配置环境变量

创建 `.env` 文件：
```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=2

# 模型配置
MODEL_DIR=./models
DEFAULT_MODEL=llama-2-7b-chat

# 性能配置
MAX_CACHE_SIZE=1000
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=20

# 监控配置
ENABLE_MONITORING=true
METRICS_PORT=9090
```

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📦 Docker 部署

### 1. Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建模型目录
RUN mkdir -p models

# 暴露端口
EXPOSE 8000 9090

# 启动命令
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

  # 可选：Redis缓存
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 3. 构建和运行
```bash
# 构建镜像
docker build -t llm-service .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -p 9090:9090 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --name llm-service \
  llm-service

# 使用docker-compose
docker-compose up -d
```

## 🔧 性能调优

### 1. 内存优化配置
```python
# 在模型加载时使用这些参数
model_params = {
    'n_ctx': 2048,           # 上下文长度
    'n_gpu_layers': 0,       # GPU层数（如有GPU）
    'n_threads': 4,          # CPU线程数
    'n_batch': 512,          # 批处理大小
    'use_mmap': True,        # 内存映射
    'use_mlock': False       # 避免内存锁定
}
```

### 2. 系统参数调优
```bash
# Linux系统优化
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
echo 'vm.swappiness = 10' >> /etc/sysctl.conf
sysctl -p

# 增加文件描述符限制
echo '* soft nofile 65535' >> /etc/security/limits.conf
echo '* hard nofile 65535' >> /etc/security/limits.conf
```

### 3. 模型量化建议
```bash
# 使用4bit量化（推荐）
# 内存占用减少约75%，性能损失约10-15%

# 使用8bit量化
# 内存占用减少约50%，性能损失约5-10%
```

## 📊 监控和日志

### 1. 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/api/v1/health

# 检查指标
curl http://localhost:8000/metrics
```

### 2. 日志配置
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

### 3. 关键监控指标
- **内存使用率**: 保持在80%以下
- **CPU使用率**: 监控峰值使用
- **请求延迟**: P95 < 5秒
- **错误率**: < 1%
- **并发连接数**: 监控活跃连接

## 🛡️ 安全配置

### 1. API认证
```python
# 添加API密钥认证
API_KEYS = {"your-secret-key": "user1"}

async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### 2. 速率限制
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/generate")
@limiter.limit("10/minute")
async def generate_text(request: Request):
    # ...
```

### 3. CORS配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 生产环境限制源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 运维脚本

### 1. 启动脚本
```bash
#!/bin/bash
# start.sh

# 设置环境
export PYTHONPATH=.
export ENV=production

# 启动服务
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

### 2. 监控脚本
```bash
#!/bin/bash
# monitor.sh

# 检查服务状态
check_service() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$response" -eq 200 ]; then
        echo "Service is healthy"
    else
        echo "Service is down, restarting..."
        # 重启逻辑
    fi
}

# 监控循环
while true; do
    check_service
    sleep 30
done
```

### 3. 日志清理脚本
```bash
#!/bin/bash
# cleanup_logs.sh

# 保留最近7天的日志
find ./logs -name "*.log" -mtime +7 -delete

# 压缩旧日志
find ./logs -name "*.log" -mtime +3 -exec gzip {} \;
```

## 📋 故障排除

### 常见问题解决
1. **内存不足**: 减少并发数或使用量化模型
2. **模型加载失败**: 检查模型文件路径和格式
3. **性能下降**: 检查系统资源使用情况
4. **连接超时**: 调整超时设置或优化网络

### 紧急恢复步骤
```bash
# 1. 停止服务
pkill -f uvicorn

# 2. 清理内存
sync && echo 3 > /proc/sys/vm/drop_caches

# 3. 重启服务
./start.sh
```

这个部署指南提供了从开发到生产的完整部署方案，包括Docker部署、性能调优、监控运维等关键内容。