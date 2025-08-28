# 🚀 llm-engine 是大模型本地化服务引擎

一个高性能的大模型本地服务引擎，支持多种开源大模型，提供OpenAI兼容的API接口和流式输出支持,是中小企业与组织给团体提供本地大模型服务的选择。

## ✨ 特性

- **多模型支持**: LLaMA、ChatGLM、Qwen、Gemma等开源大模型
- **格式兼容**: 支持GGUF、GGML、HuggingFace多种模型格式
- **OpenAI兼容**: 完全兼容OpenAI API标准，支持官方SDK直接使用
- **流式输出**: 支持SSE流式协议，完全兼容OpenAI流式接口
- **高性能**: 异步架构、内存映射、智能缓存优化
- **生产就绪**: 监控、日志、安全、部署方案完善

## 🏗️ 架构设计

### 核心组件
- **API网关层**: FastAPI异步框架
- **模型管理层**: 多模型加载和生命周期管理
- **推理服务层**: 文本生成和流式输出
- **缓存层**: 请求结果缓存和性能优化
- **监控层**: 资源使用和性能监控

### 技术栈
- **Web框架**: FastAPI + Uvicorn
- **模型推理**: llama-cpp-python + transformers
- **缓存**: 内存缓存 + Redis（可选）
- **监控**: Prometheus + 自定义指标
- **部署**: Docker + 原生部署

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
复制环境变量文件：
```bash
cp .env.example .env
```
编辑 `.env` 文件配置您的设置。

### 3. 准备模型
将模型文件放入 `models/` 目录：
```
models/
├── qwen-7b-chat.gguf
├── gemma-7b.gguf
└── llama-2-7b-chat.gguf
```

### 4. 启动服务
```bash
python run.py
```

### 5. 访问API
- 文档界面: http://localhost:8000/docs
- OpenAI兼容接口: http://localhost:8000/v1
- 健康检查: http://localhost:8000/api/v1/health

## 📋 API接口

### 自定义接口
- `POST /api/v1/generate` - 文本生成
- `POST /api/v1/generate/stream` - 流式生成
- `GET /api/v1/models` - 模型列表
- `POST /api/v1/models/{model}/load` - 加载模型

### OpenAI兼容接口
- `POST /v1/chat/completions` - 聊天补全
- `POST /v1/completions` - 文本补全
- `GET /v1/models` - 模型列表

## 🔧 配置说明

### 主要配置项
```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=2

# 模型配置
MODEL_DIR=./models
DEFAULT_MODEL=qwen-7b-chat

# 性能配置
MAX_CACHE_SIZE=1000
MAX_CONCURRENT_REQUESTS=20

# 流式配置
STREAMING_ENABLED=true
```
## 直接运行
### 下载代码
### 运行
python run.py

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t llm-service .
```

### 运行容器
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

## 📊 性能优化

### 内存优化
- 使用4bit/8bit模型量化
- 内存映射技术减少内存占用
- 智能缓存减少重复计算

### 并发优化
- 异步请求处理
- 连接池管理
- 请求批处理

### 监控指标
- 内存使用率
- 请求延迟
- 并发连接数
- 缓存命中率

## 🔍 使用示例

### Python客户端
```python
import openai

# 配置指向本地服务
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"

# 使用OpenAI SDK
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[{"role": "user", "content": "请介绍人工智能"}]
)
print(response.choices[0].message.content)
```

### JavaScript客户端
```javascript
// 流式调用示例
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/generate/stream?prompt=你好&model=qwen-7b-chat'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.token);
};
```

## 🛡️ 安全特性

- API密钥认证
- 请求速率限制
- CORS跨域支持
- 输入验证和过滤

## 📈 监控运维

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

### 性能监控
```bash
curl http://localhost:8000/metrics
```

### 日志查看
日志文件位于 `logs/` 目录，包含：
- 应用日志 (`app.log`)
- 访问日志 (`access.log`)
- 错误日志 (`error.log`)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 技术支持

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 文档: [项目Wiki](https://github.com/your-repo/wiki)
- 讨论: [Discussions](https://github.com/your-repo/discussions)

## 🎯 路线图

- [ ] 多模态模型支持
- [ ] 分布式部署
- [ ] 模型微调接口
- [ ] 高级监控告警
- [ ] Web管理界面

---

**开始使用**: 查看 [快速开始](#-快速开始) 部分立即体验！