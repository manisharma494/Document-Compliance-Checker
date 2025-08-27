import time
import logging
from typing import Callable, Any, Dict
from functools import wraps
from dataclasses import dataclass
from statistics import mean, median


@dataclass
class PerformanceMetrics:
    """Performance metrics for document processing."""
    total_time: float
    extraction_time: float
    analysis_time: float
    modification_time: float
    file_size: int
    word_count: int
    cache_hit: bool = False


class PerformanceMonitor:
    """Monitor and optimize document processing performance."""
    
    def __init__(self):
        self.metrics_history: list[PerformanceMetrics] = []
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds
        self.slow_threshold = 5.0  # seconds
        self.large_file_threshold = 10 * 1024 * 1024  # 10MB
        self.large_word_threshold = 10000  # words
    
    def monitor(self, operation: str):
        """Decorator to monitor function performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self._log_performance(operation, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._log_performance(operation, execution_time, success=False, error=str(e))
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self._log_performance(operation, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._log_performance(operation, execution_time, success=False, error=str(e))
                    raise
            
            if operation.startswith('async_'):
                return async_wrapper
            return sync_wrapper
        return decorator
    
    def _log_performance(self, operation: str, execution_time: float, success: bool, error: str = None):
        """Log performance metrics."""
        if execution_time > self.slow_threshold:
            level = logging.WARNING
            message = f"SLOW OPERATION: {operation} took {execution_time:.2f}s"
        else:
            level = logging.INFO
            message = f"Operation {operation} completed in {execution_time:.2f}s"
        
        if not success:
            level = logging.ERROR
            message += f" with error: {error}"
        
        self.logger.log(level, message)
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """Add performance metrics to history."""
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics_history:
            return {"message": "No performance data available"}
        
        times = [m.total_time for m in self.metrics_history]
        file_sizes = [m.file_size for m in self.metrics_history]
        word_counts = [m.word_count for m in self.metrics_history]
        cache_hits = sum(1 for m in self.metrics_history if m.cache_hit)
        
        return {
            "total_operations": len(self.metrics_history),
            "average_response_time": mean(times),
            "median_response_time": median(times),
            "fastest_operation": min(times),
            "slowest_operation": max(times),
            "average_file_size_mb": mean(file_sizes) / (1024 * 1024),
            "average_word_count": mean(word_counts),
            "cache_hit_rate": cache_hits / len(self.metrics_history),
            "performance_trend": self._get_performance_trend()
        }
    
    def _get_performance_trend(self) -> str:
        """Analyze performance trend over time."""
        if len(self.metrics_history) < 10:
            return "insufficient_data"
        
        recent_times = [m.total_time for m in self.metrics_history[-10:]]
        earlier_times = [m.total_time for m in self.metrics_history[-20:-10]]
        
        if len(earlier_times) < 10:
            return "insufficient_data"
        
        recent_avg = mean(recent_times)
        earlier_avg = mean(earlier_times)
        
        if recent_avg < earlier_avg * 0.9:
            return "improving"
        elif recent_avg > earlier_avg * 1.1:
            return "degrading"
        else:
            return "stable"
    
    def optimize_large_documents(self, file_size: int, word_count: int) -> Dict[str, Any]:
        """Provide optimization recommendations for large documents."""
        recommendations = []
        
        if file_size > self.large_file_threshold:
            recommendations.append("Consider splitting large documents into smaller sections")
            recommendations.append("Enable caching for repeated analysis")
        
        if word_count > self.large_word_threshold:
            recommendations.append("Process document in chunks for better performance")
            recommendations.append("Use background processing for very large documents")
        
        if not recommendations:
            recommendations.append("Document size is optimal for current processing")
        
        return {
            "file_size_mb": file_size / (1024 * 1024),
            "word_count": word_count,
            "recommendations": recommendations,
            "estimated_processing_time": self._estimate_processing_time(file_size, word_count)
        }
    
    def _estimate_processing_time(self, file_size: int, word_count: int) -> float:
        """Estimate processing time based on file characteristics."""
        # Base processing time per MB
        base_time_per_mb = 0.5  # seconds
        
        # Additional time per 1000 words
        time_per_1000_words = 0.2  # seconds
        
        estimated_time = (file_size / (1024 * 1024)) * base_time_per_mb + (word_count / 1000) * time_per_1000_words
        
        return min(estimated_time, 30.0)  # Cap at 30 seconds
