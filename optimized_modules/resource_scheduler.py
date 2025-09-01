"""
智能资源调度系统
实现动态资源分配、负载均衡和自动扩缩容
优化系统性能和资源利用率
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import psutil
import json
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import heapq

from .performance_monitor import metrics_collector, tracker

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"

class Priority(Enum):
    """任务优先级枚举"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class ResourceRequirement:
    """资源需求"""
    cpu_cores: float = 0.1
    memory_mb: int = 100
    disk_mb: int = 50
    gpu_memory_mb: int = 0
    network_bandwidth: float = 1.0

@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    priority: Priority
    resource_requirement: ResourceRequirement
    created_at: float = field(default_factory=time.time)
    estimated_duration: float = 30.0  # 秒
    dependencies: List[str] = field(default_factory=list)
    callback: Optional[callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """优先级比较"""
        return self.priority.value < other.priority.value

@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float = 0.0
    memory_mb: int = 0
    disk_mb: int = 0
    gpu_memory_mb: int = 0
    network_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        self.current_usage = ResourceUsage()
        self.usage_history = deque(maxlen=1000)
        self.monitoring_thread = None
        self.is_monitoring = False
        self._lock = threading.Lock()
        
    def start_monitoring(self):
        """开始资源监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """停止资源监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                usage = self._get_current_usage()
                with self._lock:
                    self.current_usage = usage
                    self.usage_history.append(usage)
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
    
    def _get_current_usage(self) -> ResourceUsage:
        """获取当前资源使用"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用
        memory = psutil.virtual_memory()
        memory_mb = memory.used // (1024 * 1024)
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        disk_mb = disk.used // (1024 * 1024)
        
        # 网络使用
        net_io = psutil.net_io_counters()
        network_mb = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            disk_mb=disk_mb,
            network_mb=network_mb
        )
    
    def get_available_resources(self) -> ResourceRequirement:
        """获取可用资源"""
        with self._lock:
            usage = self.current_usage
        
        # 获取系统总资源
        cpu_count = psutil.cpu_count()
        memory_total = psutil.virtual_memory().total // (1024 * 1024)
        disk_total = psutil.disk_usage('/').total // (1024 * 1024)
        
        # 计算可用资源
        available_cpu = max(0.1, cpu_count * (1 - usage.cpu_percent / 100))
        available_memory = max(100, memory_total - usage.memory_mb)
        available_disk = max(50, disk_total - usage.disk_mb)
        
        return ResourceRequirement(
            cpu_cores=available_cpu,
            memory_mb=available_memory,
            disk_mb=available_disk,
            gpu_memory_mb=0  # 暂不支持GPU
        )
    
    def get_usage_trend(self, minutes: int = 5) -> Dict[str, float]:
        """获取资源使用趋势"""
        cutoff_time = time.time() - (minutes * 60)
        
        with self._lock:
            recent_usage = [
                u for u in self.usage_history 
                if u.timestamp > cutoff_time
            ]
        
        if len(recent_usage) < 2:
            return {}
        
        # 计算趋势
        cpu_trend = recent_usage[-1].cpu_percent - recent_usage[0].cpu_percent
        memory_trend = recent_usage[-1].memory_mb - recent_usage[0].memory_mb
        
        return {
            'cpu_trend_percent': cpu_trend,
            'memory_trend_mb': memory_trend,
            'trend_direction': 'increasing' if cpu_trend > 0 else 'decreasing'
        }

class TaskQueue:
    """智能任务队列"""
    
    def __init__(self):
        self.queues: Dict[Priority, List[Task]] = defaultdict(list)
        self.task_map: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, bool] = {}
        self._lock = threading.RLock()
    
    def add_task(self, task: Task) -> bool:
        """添加任务到队列"""
        with self._lock:
            if task.task_id in self.task_map:
                return False
            
            self.queues[task.priority].append(task)
            self.task_map[task.task_id] = task
            heapq.heapify(self.queues[task.priority])
            return True
    
    def get_next_task(self) -> Optional[Task]:
        """获取下一个可执行的任务"""
        with self._lock:
            # 按优先级获取任务
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW, Priority.BACKGROUND]:
                if self.queues[priority]:
                    task = heapq.heappop(self.queues[priority])
                    
                    # 检查依赖
                    if all(dep in self.completed_tasks for dep in task.dependencies):
                        return task
                    else:
                        # 重新放回队列
                        self.queues[priority].append(task)
                        heapq.heapify(self.queues[priority])
            
            return None
    
    def mark_completed(self, task_id: str):
        """标记任务完成"""
        with self._lock:
            self.completed_tasks[task_id] = True
            if task_id in self.task_map:
                del self.task_map[task_id]
    
    def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计"""
        with self._lock:
            stats = {}
            for priority in Priority:
                stats[priority.name] = len(self.queues[priority])
            stats['total'] = len(self.task_map)
            return stats

class ResourceScheduler:
    """智能资源调度器"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.resource_monitor = ResourceMonitor()
        self.task_queue = TaskQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self._lock = threading.RLock()
        self.is_running = False
        self.scheduler_thread = None
        
        # 资源限制
        self.resource_limits = {
            'max_cpu_percent': 80.0,
            'max_memory_percent': 80.0,
            'min_free_memory_mb': 1024
        }
        
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.is_running = True
            self.resource_monitor.start_monitoring()
            self.scheduler_thread = threading.Thread(
                target=self._scheduling_loop, daemon=True
            )
            self.scheduler_thread.start()
            logger.info("Resource scheduler started")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        self.resource_monitor.stop_monitoring()
        self.executor.shutdown(wait=True)
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Resource scheduler stopped")
    
    def submit_task(self, task: Task) -> str:
        """提交任务"""
        if self.task_queue.add_task(task):
            logger.info(f"Task {task.task_id} submitted with priority {task.priority.name}")
            return task.task_id
        else:
            raise ValueError(f"Task {task.task_id} already exists")
    
    def can_execute_task(self, task: Task) -> bool:
        """检查是否可以执行任务"""
        # 检查当前活跃任务数
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return False
        
        # 检查资源可用性
        available = self.resource_monitor.get_available_resources()
        
        return (
            available.cpu_cores >= task.resource_requirement.cpu_cores and
            available.memory_mb >= task.resource_requirement.memory_mb and
            available.disk_mb >= task.resource_requirement.disk_mb
        )
    
    def _scheduling_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                # 获取下一个任务
                task = self.task_queue.get_next_task()
                if task and self.can_execute_task(task):
                    # 执行任务
                    self._execute_task(task)
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"Scheduling error: {e}")
                time.sleep(5)
    
    def _execute_task(self, task: Task):
        """执行任务"""
        def run_task():
            with tracker.track_operation(
                f"task_{task.task_type}", 
                metadata={
                    'task_id': task.task_id,
                    'priority': task.priority.name,
                    'estimated_duration': task.estimated_duration
                }
            ):
                try:
                    if task.callback:
                        task.callback(task)
                    
                    logger.info(f"Task {task.task_id} completed successfully")
                    
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    raise
                finally:
                    with self._lock:
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]
                        self.task_queue.mark_completed(task.task_id)
        
        with self._lock:
            self.active_tasks[task.task_id] = task
        
        self.executor.submit(run_task)
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """获取调度器统计"""
        with self._lock:
            stats = {
                'active_tasks': len(self.active_tasks),
                'queue_stats': self.task_queue.get_queue_stats(),
                'available_resources': asdict(self.resource_monitor.get_available_resources()),
                'system_usage': asdict(self.resource_monitor.current_usage),
                'usage_trend': self.resource_monitor.get_usage_trend()
            }
        return stats
    
    def adjust_concurrency(self, new_max: int):
        """动态调整并发度"""
        with self._lock:
            self.max_concurrent_tasks = max(1, min(new_max, 50))
            self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
            logger.info(f"Concurrency adjusted to {self.max_concurrent_tasks}")

class AutoScaler:
    """自动扩缩容器"""
    
    def __init__(self, scheduler: ResourceScheduler):
        self.scheduler = scheduler
        self.scaling_rules = {
            'cpu_threshold_high': 70.0,
            'cpu_threshold_low': 20.0,
            'memory_threshold_high': 75.0,
            'memory_threshold_low': 25.0,
            'queue_size_threshold': 10,
            'scale_up_factor': 1.5,
            'scale_down_factor': 0.8,
            'min_concurrent': 2,
            'max_concurrent': 50
        }
        self.is_monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval_seconds: int = 30):
        """开始自动扩缩容监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._scaling_loop, 
                args=(interval_seconds,),
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("Auto-scaler started")
    
    def stop_monitoring(self):
        """停止自动扩缩容监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Auto-scaler stopped")
    
    def _scaling_loop(self, interval_seconds: int):
        """扩缩容循环"""
        while self.is_monitoring:
            try:
                self._evaluate_scaling()
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                time.sleep(interval_seconds * 2)
    
    def _evaluate_scaling(self):
        """评估扩缩容需求"""
        stats = self.scheduler.get_scheduler_stats()
        
        # 获取系统指标
        current_usage = stats['system_usage']
        queue_size = stats['queue_stats']['total']
        
        # 计算扩缩容因子
        scale_factor = 1.0
        
        # CPU使用率
        if current_usage['cpu_percent'] > self.scaling_rules['cpu_threshold_high']:
            scale_factor *= self.scaling_rules['scale_up_factor']
        elif current_usage['cpu_percent'] < self.scaling_rules['cpu_threshold_low']:
            scale_factor *= self.scaling_rules['scale_down_factor']
        
        # 内存使用率
        if current_usage['memory_mb'] > self.scaling_rules['memory_threshold_high'] * 1000:  # 假设总内存1000MB
            scale_factor *= self.scaling_rules['scale_up_factor']
        elif current_usage['memory_mb'] < self.scaling_rules['memory_threshold_low'] * 1000:
            scale_factor *= self.scaling_rules['scale_down_factor']
        
        # 队列大小
        if queue_size > self.scaling_rules['queue_size_threshold']:
            scale_factor *= self.scaling_rules['scale_up_factor']
        
        # 计算新的并发度
        current_max = self.scheduler.max_concurrent_tasks
        new_max = max(
            self.scaling_rules['min_concurrent'],
            min(
                int(current_max * scale_factor),
                self.scaling_rules['max_concurrent']
            )
        )
        
        # 调整并发度
        if new_max != current_max:
            self.scheduler.adjust_concurrency(new_max)
            logger.info(f"Auto-scaled from {current_max} to {new_max} concurrent tasks")

# 全局实例
scheduler = ResourceScheduler(max_concurrent_tasks=5)
auto_scaler = AutoScaler(scheduler)

# 使用示例
async def example_usage():
    """使用示例"""
    
    # 启动调度器
    scheduler.start()
    auto_scaler.start_monitoring()
    
    # 创建示例任务
    task = Task(
        task_id="example_task_1",
        task_type="video_processing",
        priority=Priority.NORMAL,
        resource_requirement=ResourceRequirement(
            cpu_cores=0.5,
            memory_mb=200,
            disk_mb=100
        ),
        callback=lambda t: print(f"任务 {t.task_id} 完成")
    )
    
    # 提交任务
    task_id = scheduler.submit_task(task)
    print(f"任务已提交: {task_id}")
    
    # 获取统计信息
    stats = scheduler.get_scheduler_stats()
    print("调度器统计:", json.dumps(stats, indent=2, default=str))
    
    # 等待任务完成
    await asyncio.sleep(5)
    
    # 停止调度器
    auto_scaler.stop_monitoring()
    scheduler.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())