# 动态内存管理功能指南

## 📋 功能概述

动态内存管理功能实现了对大模型服务引擎的内存使用进行智能监控和优化，主要包括：

- ✅ **内存使用监控**：实时监控模型内存使用和系统内存状态
- ✅ **LRU缓存淘汰**：基于最近最少使用原则自动卸载不常用模型
- ✅ **内存压力检测**：自动检测内存压力并推荐清理策略
- ✅ **API管理接口**：提供完整的RESTful API进行内存管理
- ✅ **自动清理机制**：支持手动和自动内存清理

## 🚀 快速开始

### 1. 启动服务

```bash
# 在虚拟环境下启动
python run.py
```

### 2. 测试内存管理功能

```bash
python test_memory_manager.py
```

### 3. 使用API接口

#### 查看内存统计
```bash
curl http://localhost:8080/api/v1/memory/stats
```

#### 检查内存压力
```bash
curl http://localhost:8080/api/v1/memory/pressure
```

#### 清理内存
```bash
curl -X POST http://localhost:8080/api/v1/memory/cleanup
```

#### 查看模型内存使用
```bash
curl http://localhost:8080/api/v1/memory/models
```

#### 设置内存限制
```bash
curl -X POST "http://localhost:8080/api/v1/memory/limit?limit_gb=4.0"
```

## 📊 API接口详情

### GET `/api/v1/memory/stats`
获取内存统计信息，包括总内存使用、内存限制、内存压力状态等。

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "total_models": 2,
    "total_memory_usage": 2147483648,
    "formatted_usage": "2.00 GB",
    "memory_limit": 8589934592,
    "formatted_limit": "8.00 GB",
    "memory_pressure": false,
    "system_available": 17179869184,
    "formatted_system_available": "16.00 GB",
    "system_total": 34359738368,
    "formatted_system_total": "32.00 GB"
  }
}
```

### GET `/api/v1/memory/pressure`
检查内存压力状态，返回是否需要清理和推荐清理的模型列表。

### POST `/api/v1/memory/cleanup`
执行内存清理，卸载不常用的模型以释放内存。

### GET `/api/v1/memory/models`
列出所有模型的内存使用情况，包括加载状态、文件大小、访问统计等。

### POST `/api/v1/memory/limit`
设置内存使用限制（单位：GB）。

### GET `/api/v1/memory/system`
获取系统内存信息，包括物理内存和交换空间使用情况。

## ⚙️ 配置选项

在 `.env` 文件中可以配置以下参数：

```env
# 内存管理配置
MAX_MEMORY_USAGE=8589934592    # 最大内存使用限制（字节）
MEMORY_CHECK_INTERVAL=60       # 内存检查间隔（秒）
AUTO_CLEANUP_ENABLED=true      # 是否启用自动清理
```

## 🎯 性能优化建议

### 1. 合理设置内存限制
根据系统可用内存设置适当的内存限制，建议为系统总内存的70-80%。

### 2. 监控内存使用趋势
定期检查内存统计信息，了解模型内存使用模式。

### 3. 使用自动清理
启用自动清理功能，让系统在内存压力时自动卸载不常用模型。

### 4. 模型加载策略
- 优先加载常用模型
- 及时卸载长时间不用的模型
- 考虑模型大小和使用频率的平衡

## 🔧 故障排除

### 内存清理失败
- 检查模型是否正在被使用
- 确认模型管理器状态正常

### 内存统计不准确
- 确保 `psutil` 库正确安装
- 检查系统权限是否足够

### 自动清理不触发
- 检查内存限制设置是否合理
- 确认自动清理功能已启用

## 📈 监控指标

| 指标 | 描述 | 正常范围 |
|------|------|----------|
| 内存使用率 | 已使用内存占总限制的比例 | <80% |
| 系统可用内存 | 系统剩余可用内存 | >2GB |
| 模型加载数 | 当前加载的模型数量 | 根据内存调整 |
| 缓存命中率 | 内存清理后重新加载的频率 | 越低越好 |

## 🚨 注意事项

1. **生产环境部署**：建议在生产环境中设置合理的内存限制和监控告警
2. **重要模型保护**：对于关键业务模型，考虑实现免清理保护机制
3. **性能监控**：定期检查内存管理对服务性能的影响
4. **日志分析**：关注内存清理日志，优化模型使用策略

## 📝 版本历史

- **v0.1.0** (2024-01-29): 初始版本，实现基础动态内存管理功能
- 支持内存监控和LRU缓存淘汰
- 提供完整的RESTful API接口
- 集成系统内存信息获取

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进内存管理功能，特别是在：
- 内存估算算法的准确性
- 自动清理策略的优化
- 监控和告警功能的增强