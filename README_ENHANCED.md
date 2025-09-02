# 增强版 CapCut API 服务器

## 项目概述

增强版 CapCut API 服务器是对原始 CapCut API 的性能优化版本，集成了全面的性能监控、资源追踪和优化配置功能。该版本保留了原始 API 的核心功能，同时添加了先进的性能管理特性，适用于生产环境和高负载场景。

## 主要特性

### 1. 性能监控系统

- **实时指标收集**：追踪 CPU、内存、磁盘和网络使用情况
- **请求性能分析**：监控请求处理时间、慢请求识别和资源消耗
- **分布式追踪**：支持 OpenTelemetry 集成（如果可用）
- **性能仪表板**：通过 API 端点提供实时性能数据

### 2. 高级配置选项

- **异步处理**：线程池大小、任务队列配置
- **缓存管理**：TTL、最大缓存大小、清理间隔
- **压缩优化**：可配置的压缩级别和阈值
- **超时与重试**：自动重试机制和超时控制
- **限流保护**：请求速率限制和突发流量处理

### 3. 监控与告警

- **性能追踪**：自动识别性能瓶颈
- **慢请求日志**：记录并分析超过阈值的请求
- **资源使用告警**：当系统资源接近阈值时触发告警
- **健康状态检查**：提供详细的系统健康报告

## 项目结构

```
CapCutAPI/
├── enhanced_server.py          # 增强版服务器主文件
├── run_enhanced_server.py      # 服务器启动脚本
├── test_enhanced_server.py     # 性能测试脚本
├── config.py                   # 配置文件（包含优化配置）
├── optimized_modules/
│   ├── performance_monitor.py  # 性能监控核心模块
│   ├── performance_api.py      # 性能监控 API 端点
│   └── performance_middleware.py # 性能监控中间件
└── README_ENHANCED.md          # 本文档
```

## 安装与依赖

### 依赖项

```
flask>=2.0.0
requests>=2.25.0
psutil>=5.8.0
numpy>=1.20.0
opentelemetry-api>=1.0.0  # 可选，用于分布式追踪
opentelemetry-sdk>=1.0.0  # 可选，用于分布式追踪
```

### 安装步骤

1. 克隆仓库或下载源代码
2. 安装依赖：`pip install -r requirements.txt`

## 使用方法

### 启动服务器

使用启动脚本运行服务器：

```bash
python run_enhanced_server.py --host 0.0.0.0 --port 5000 --debug
```

参数说明：
- `--host`：服务器主机地址，默认为 0.0.0.0
- `--port`：服务器端口，默认为 5000
- `--debug`：启用调试模式

### 性能测试

使用测试脚本测试服务器性能：

```bash
python test_enhanced_server.py --host localhost --port 5000 --requests 100 --concurrency 10
```

参数说明：
- `--host`：服务器主机地址，默认为 localhost
- `--port`：服务器端口，默认为 5000
- `--requests`：发送的请求数量，默认为 100
- `--concurrency`：并发请求数量，默认为 10

## API 端点

### 基础端点

- `GET /`：服务器首页，返回基本信息
- `GET /health`：健康检查，返回系统健康状态
- `GET /status`：服务器状态，返回详细运行状态
- `POST /echo`：回显测试，将请求数据回显给客户端

### 性能监控端点

所有性能监控端点都以 `/api/v1/performance` 为前缀：

- `GET /api/v1/performance/health`：获取系统健康状态
- `GET /api/v1/performance/stats`：获取性能统计信息
- `GET /api/v1/performance/dashboard`：获取性能仪表板数据
- `GET /api/v1/performance/operations`：获取操作性能分解数据
- `GET /api/v1/performance/alerts/thresholds`：获取告警阈值
- `POST /api/v1/performance/alerts/thresholds`：更新告警阈值
- `GET /api/v1/performance/active-requests`：获取当前活跃请求
- `GET /api/v1/performance/slow-requests`：获取慢请求列表
- `GET /api/v1/performance/resource-usage`：获取资源使用情况

## 配置选项

在 `config.py` 文件中，`OptimizationConfig` 类提供了以下配置选项：

### 异步处理

- `thread_pool_size`：线程池大小
- `task_queue_size`：任务队列大小
- `large_file_threshold`：大文件阈值（字节）

### 缓存

- `cache_ttl`：缓存生存时间（秒）
- `max_cache_size`：最大缓存大小（项）
- `cache_cleanup_interval`：缓存清理间隔（秒）

### 性能优化

- `compression_level`：压缩级别（0-9）
- `compression_min_size`：最小压缩大小（字节）

### 超时与重试

- `retry_count`：重试次数
- `retry_delay`：重试延迟（秒）
- `request_timeout`：请求超时（秒）

### 限流

- `enable_rate_limiting`：启用限流
- `rate_limit_per_minute`：每分钟请求限制
- `rate_limit_burst`：突发请求限制

### 监控与日志

- `enable_performance_tracking`：启用性能追踪
- `log_slow_requests`：记录慢请求
- `slow_request_threshold`：慢请求阈值（秒）

## 性能监控系统

### 核心组件

- **MetricsCollector**：收集系统和操作性能指标
- **PerformanceTracker**：追踪操作性能
- **AlertManager**：管理性能告警
- **PerformanceDashboard**：提供性能数据可视化

### 监控中间件

`PerformanceMiddleware` 自动监控所有 Flask 请求，记录请求时间、响应状态和资源使用情况。

### 使用示例

```python
# 使用性能追踪装饰器
from optimized_modules.performance_monitor import monitor_sync, monitor_async

@monitor_sync(operation_name="example_operation")
def example_function():
    # 函数实现
    pass

@monitor_async(operation_name="example_async_operation")
async def example_async_function():
    # 异步函数实现
    pass
```

## 贡献指南

欢迎提交问题报告、功能请求和代码贡献。请确保遵循以下准则：

1. 遵循现有的代码风格和命名约定
2. 为新功能添加适当的测试
3. 更新文档以反映您的更改

## 许可证

[MIT License](LICENSE)