"""
性能监控与追踪系统
基于OpenTelemetry实现全面的可观测性
包括指标收集、分布式追踪、实时监控和告警
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from functools import wraps
import threading
import psutil
import os

# OpenTelemetry 导入
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.system_metrics import SystemMetrics
    from opentelemetry.metrics import Observation
    
    # 配置OpenTelemetry
    resource = Resource(attributes={
        "service.name": "capcut-api",
        "service.version": "1.0.0",
        "service.namespace": "capcut"
    })
    
    # 配置追踪
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # 配置指标
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True),
        export_interval_millis=5000
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    meter = metrics.get_meter(__name__)
    
    OTEL_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("OpenTelemetry not available, using fallback monitoring")
    OTEL_AVAILABLE = False
    tracer = None
    meter = None

@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: float
    operation: str
    duration: float
    memory_usage: int
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics_buffer: List[PerformanceMetrics] = []
        self.buffer_lock = threading.Lock()
        self.is_collecting = True
        
        # 系统指标
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_usage': 0,
            'disk_usage': 0.0,
            'network_io': (0, 0)
        }
        
        # 启动系统监控线程
        self.monitoring_thread = threading.Thread(target=self._system_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # OpenTelemetry指标
        if OTEL_AVAILABLE:
            self._setup_otel_metrics()
    
    def _setup_otel_metrics(self):
        """设置OpenTelemetry指标"""
        if not OTEL_AVAILABLE:
            return
        
        # 计数器
        self.operation_counter = meter.create_counter(
            "capcut_operations_total",
            description="Total number of operations",
            unit="1"
        )
        
        # 直方图
        self.duration_histogram = meter.create_histogram(
            "capcut_operation_duration_seconds",
            description="Duration of operations in seconds",
            unit="s"
        )
        
        # 内存使用
        self.memory_usage_gauge = meter.create_observable_gauge(
            "capcut_memory_usage_bytes",
            description="Current memory usage in bytes",
            unit="bytes",
            callbacks=[self._get_memory_usage]
        )
        
        # CPU使用
        self.cpu_usage_gauge = meter.create_observable_gauge(
            "capcut_cpu_usage_percent",
            description="Current CPU usage percentage",
            unit="percent",
            callbacks=[self._get_cpu_usage]
        )
    
    def _get_memory_usage(self, observer):
        """获取内存使用"""
        memory = psutil.virtual_memory()
        yield Observation(memory.used)
    
    def _get_cpu_usage(self, observer):
        """获取CPU使用"""
        cpu_percent = psutil.cpu_percent(interval=1)
        yield Observation(cpu_percent)
    
    def _system_monitoring_loop(self):
        """系统监控循环"""
        while self.is_collecting:
            try:
                # CPU使用率
                self.system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
                
                # 内存使用
                memory = psutil.virtual_memory()
                self.system_metrics['memory_usage'] = memory.used
                
                # 磁盘使用
                disk = psutil.disk_usage('/')
                self.system_metrics['disk_usage'] = (disk.used / disk.total) * 100
                
                # 网络IO
                net_io = psutil.net_io_counters()
                self.system_metrics['network_io'] = (net_io.bytes_sent, net_io.bytes_recv)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
            
            time.sleep(5)  # 每5秒更新一次
    
    def record_metric(self, operation: str, duration: float, success: bool = True, 
                     error_message: Optional[str] = None, metadata: Dict[str, Any] = None):
        """记录性能指标"""
        metric = PerformanceMetrics(
            timestamp=time.time(),
            operation=operation,
            duration=duration,
            memory_usage=self.system_metrics['memory_usage'],
            cpu_usage=self.system_metrics['cpu_percent'],
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        with self.buffer_lock:
            self.metrics_buffer.append(metric)
            
            # 限制缓冲区大小
            if len(self.metrics_buffer) > 10000:
                self.metrics_buffer = self.metrics_buffer[-5000:]
        
        # OpenTelemetry指标
        if OTEL_AVAILABLE:
            labels = {"operation": operation, "success": str(success)}
            self.operation_counter.add(1, labels)
            self.duration_histogram.record(duration, labels)
    
    def get_metrics_summary(self, operation: str = None, last_n_minutes: int = 60) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = time.time() - (last_n_minutes * 60)
        
        with self.buffer_lock:
            relevant_metrics = [
                m for m in self.metrics_buffer 
                if m.timestamp > cutoff_time and (operation is None or m.operation == operation)
            ]
        
        if not relevant_metrics:
            return {}
        
        # 计算统计信息
        durations = [m.duration for m in relevant_metrics]
        success_count = sum(1 for m in relevant_metrics if m.success)
        
        return {
            'total_operations': len(relevant_metrics),
            'success_rate': (success_count / len(relevant_metrics)) * 100,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)],
            'p99_duration': sorted(durations)[int(len(durations) * 0.99)],
            'current_memory_mb': self.system_metrics['memory_usage'] / (1024 * 1024),
            'current_cpu_percent': self.system_metrics['cpu_percent'],
            'current_disk_percent': self.system_metrics['disk_usage']
        }
    
    def get_system_health(self) -> Dict[str, str]:
        """获取系统健康状态"""
        health_status = "healthy"
        
        # 检查内存使用
        if self.system_metrics['memory_usage'] > 4 * 1024 * 1024 * 1024:  # 4GB
            health_status = "warning"
        
        # 检查CPU使用
        if self.system_metrics['cpu_percent'] > 90:
            health_status = "critical"
        
        # 检查磁盘使用
        if self.system_metrics['disk_usage'] > 90:
            health_status = "critical"
        
        return {
            'status': health_status,
            'memory_usage_mb': f"{self.system_metrics['memory_usage'] / (1024 * 1024):.2f}",
            'cpu_usage_percent': f"{self.system_metrics['cpu_percent']:.2f}",
            'disk_usage_percent': f"{self.system_metrics['disk_usage']:.2f}",
            'network_sent_mb': f"{self.system_metrics['network_io'][0] / (1024 * 1024):.2f}",
            'network_recv_mb': f"{self.system_metrics['network_io'][1] / (1024 * 1024):.2f}"
        }

class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.active_spans: Dict[str, Any] = {}
    
    @contextmanager
    def track_operation(self, operation: str, metadata: Dict[str, Any] = None):
        """追踪操作的上下文管理器"""
        start_time = time.time()
        
        # OpenTelemetry span
        span = None
        if OTEL_AVAILABLE:
            span = tracer.start_span(operation)
            if metadata:
                for key, value in metadata.items():
                    span.set_attribute(key, str(value))
        
        try:
            yield
            duration = time.time() - start_time
            self.metrics_collector.record_metric(operation, duration, True, metadata=metadata)
            
            if span:
                span.set_status(Status(StatusCode.OK))
                span.end()
                
        except Exception as e:
            duration = time.time() - start_time
            self.metrics_collector.record_metric(
                operation, duration, False, str(e), metadata
            )
            
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.end()
            
            raise
    
    async def track_async_operation(self, operation: str, coro, metadata: Dict[str, Any] = None):
        """追踪异步操作的装饰器"""
        start_time = time.time()
        
        span = None
        if OTEL_AVAILABLE:
            span = tracer.start_span(operation)
            if metadata:
                for key, value in metadata.items():
                    span.set_attribute(key, str(value))
        
        try:
            result = await coro
            duration = time.time() - start_time
            self.metrics_collector.record_metric(operation, duration, True, metadata=metadata)
            
            if span:
                span.set_status(Status(StatusCode.OK))
                span.end()
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.metrics_collector.record_metric(
                operation, duration, False, str(e), metadata
            )
            
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.end()
            
            raise

class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_handlers: List[Callable] = []
        self.alert_thresholds = {
            'error_rate': 5.0,  # 5%
            'response_time': 10.0,  # 10秒
            'memory_usage': 80.0,  # 80%
            'cpu_usage': 90.0  # 90%
        }
        self.monitoring_task = None
    
    def add_alert_handler(self, handler: Callable):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    async def check_alerts(self):
        """检查告警条件"""
        try:
            # 获取最近5分钟的指标
            summary = self.metrics_collector.get_metrics_summary(last_n_minutes=5)
            
            if not summary:
                return
            
            alerts = []
            
            # 错误率告警
            if summary.get('success_rate', 100) < (100 - self.alert_thresholds['error_rate']):
                alerts.append({
                    'type': 'error_rate',
                    'level': 'warning',
                    'message': f"Error rate is {100 - summary['success_rate']:.1f}%",
                    'value': summary['success_rate']
                })
            
            # 响应时间告警
            if summary.get('avg_duration', 0) > self.alert_thresholds['response_time']:
                alerts.append({
                    'type': 'response_time',
                    'level': 'warning',
                    'message': f"Average response time is {summary['avg_duration']:.2f}s",
                    'value': summary['avg_duration']
                })
            
            # 内存使用告警
            if summary.get('current_memory_percent', 0) > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_usage',
                    'level': 'critical',
                    'message': f"Memory usage is {summary['current_memory_percent']:.1f}%",
                    'value': summary['current_memory_percent']
                })
            
            # CPU使用告警
            if summary.get('current_cpu_percent', 0) > self.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_usage',
                    'level': 'critical',
                    'message': f"CPU usage is {summary['current_cpu_percent']:.1f}%",
                    'value': summary['current_cpu_percent']
                })
            
            # 触发告警处理器
            for alert in alerts:
                for handler in self.alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")
        
        except Exception as e:
            logger.error(f"Alert checking error: {e}")
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """启动持续监控"""
        while True:
            await self.check_alerts()
            await asyncio.sleep(interval_seconds)

class PerformanceDashboard:
    """性能仪表板"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时统计"""
        return {
            'system_health': self.metrics_collector.get_system_health(),
            'last_5_minutes': self.metrics_collector.get_metrics_summary(last_n_minutes=5),
            'last_15_minutes': self.metrics_collector.get_metrics_summary(last_n_minutes=15),
            'last_hour': self.metrics_collector.get_metrics_summary(last_n_minutes=60),
            'timestamp': time.time()
        }
    
    def get_operation_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """获取操作分解统计"""
        operations = ['create_draft', 'add_video', 'add_audio', 'export_video', 'cache_operation']
        breakdown = {}
        
        for op in operations:
            stats = self.metrics_collector.get_metrics_summary(operation=op, last_n_minutes=60)
            if stats:
                breakdown[op] = stats
        
        return breakdown

# 全局实例
metrics_collector = MetricsCollector()
tracker = PerformanceTracker(metrics_collector)
alert_manager = AlertManager(metrics_collector)
dashboard = PerformanceDashboard(metrics_collector)

# 装饰器
async def monitor_async(operation: str, metadata: Dict[str, Any] = None):
    """异步监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await tracker.track_async_operation(
                operation, 
                func(*args, **kwargs), 
                metadata
            )
        return wrapper
    return decorator

def monitor_sync(operation: str, metadata: Dict[str, Any] = None):
    """同步监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracker.track_operation(operation, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
async def example_usage():
    """使用示例"""
    
    # 添加告警处理器
    async def email_alert_handler(alert):
        print(f"📧 发送告警邮件: {alert}")
    
    alert_manager.add_alert_handler(email_alert_handler)
    
    # 启动监控
    asyncio.create_task(alert_manager.start_monitoring())
    
    # 获取实时统计
    stats = dashboard.get_realtime_stats()
    print("实时统计:", stats)
    
    # 获取操作分解
    breakdown = dashboard.get_operation_breakdown()
    print("操作分解:", breakdown)

if __name__ == "__main__":
    asyncio.run(example_usage())