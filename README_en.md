# 🚀 llm-engine - Local Large Language Model Service Engine

A high-performance local service engine for large language models, supporting various open-source models and providing OpenAI-compatible API interfaces with streaming output support.

## ✨ Features

- **Multi-Model Support**: LLaMA, ChatGLM, Qwen, Gemma, and other open-source models
- **Format Compatibility**: Supports GGUF, GGML, HuggingFace model formats
- **OpenAI Compatible**: Fully compatible with OpenAI API standards, supports direct use of official SDK
- **Streaming Output**: Supports SSE streaming protocol, fully compatible with OpenAI streaming interface
- **High Performance**: Asynchronous architecture, memory mapping, intelligent cache optimization
- **Production Ready**: Complete monitoring, logging, security, and deployment solutions

## 🏗️ Architecture Design

### Core Components
- **API Gateway Layer**: FastAPI async framework
- **Model Management Layer**: Multi-model loading and lifecycle management
- **Inference Service Layer**: Text generation and streaming output
- **Cache Layer**: Request result caching and performance optimization
- **Monitoring Layer**: Resource usage and performance monitoring

### Technology Stack
- **Web Framework**: FastAPI + Uvicorn
- **Model Inference**: llama-cpp-python + transformers
- **Cache**: Memory cache + Redis (optional)
- **Monitoring**: Prometheus + Custom metrics
- **Deployment**: Docker + Native deployment

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy the environment variable file:
```bash
cp .env.example .env
```
Edit the `.env` file to configure your settings.

### 3. Prepare Models
Place model files in the `models/` directory:
```
models/
├── qwen-7b-chat.gguf
├── gemma-7b.gguf
└── llama-2-7b-chat.gguf
```

### 4. Start Service
```bash
python run.py
```

### 5. Access API
- Documentation interface: http://localhost:8000/docs
- OpenAI compatible interface: http://localhost:8000/v1
- Health check: http://localhost:8000/api/v1/health

## 📋 API Interfaces

### Custom Interfaces
- `POST /api/v1/generate` - Text generation
- `POST /api/v1/generate/stream` - Stream generation
- `GET /api/v1/models` - Model list
- `POST /api/v1/models/{model}/load` - Load model

### OpenAI Compatible Interfaces
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- `GET /v1/models` - Model list

## 🔧 Configuration

### Main Configuration Items
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2

# Model Configuration
MODEL_DIR=./models
DEFAULT_MODEL=qwen-7b-chat

# Performance Configuration
MAX_CACHE_SIZE=1000
MAX_CONCURRENT_REQUESTS=20

# Streaming Configuration
STREAMING_ENABLED=true
```
## Direct Execution
### Download Code
### Run
python run.py

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t llm-service .
```

### Run Container
```bash
docker run -d \
  -p 8000:8000 \
  -p 9090:9090 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --name llm-service \
  llm-service
```

### Docker Compose
```bash
docker-compose up -d
```

## 📊 Performance Optimization

### Memory Optimization
- Use 4bit/8bit model quantization
- Memory mapping technology to reduce memory usage
- Intelligent caching to reduce repeated calculations

### Concurrency Optimization
- Asynchronous request processing
- Connection pool management
- Request batching

### Monitoring Metrics
- Memory usage
- Request latency
- Concurrent connections
- Cache hit rate

## 🔍 Usage Examples

### Python Client
```python
import openai

# Configure to point to local service
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"

# Use OpenAI SDK
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[{"role": "user", "content": "Please introduce artificial intelligence"}]
)
print(response.choices[0].message.content)
```

### JavaScript Client
```javascript
// Streaming call example
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/generate/stream?prompt=hello&model=qwen-7b-chat'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.token);
};
```

## 🛡️ Security Features

- API key authentication
- Request rate limiting
- CORS support
- Input validation and filtering

## 📈 Monitoring and Operations

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Performance Monitoring
```bash
curl http://localhost:8000/metrics
```

### Log Viewing
Log files are located in the `logs/` directory, including:
- Application log (`app.log`)
- Access log (`access.log`)
- Error log (`error.log`)

## 🤝 Contribution Guide

1. Fork the project
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Technical Support

- Submit Issue: [GitHub Issues](https://github.com/your-repo/issues)
- Documentation: [Project Wiki](https://github.com/your-repo/wiki)
- Discussions: [Discussions](https://github.com/your-repo/discussions)

## 🎯 Roadmap

- [ ] Multi-modal model support
- [ ] Distributed deployment
- [ ] Model fine-tuning interface
- [ ] Advanced monitoring alerts
- [ ] Web management interface

---

**Get Started**: Check out the [Quick Start](#-quick-start) section to begin!
