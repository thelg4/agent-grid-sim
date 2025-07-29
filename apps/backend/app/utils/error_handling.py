# apps/backend/app/utils/error_handling.py

import logging
import time
import traceback
import functools
from typing import Callable, Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    LLM_API = "llm_api"
    AGENT_LOGIC = "agent_logic"
    GRID_OPERATION = "grid_operation"
    COORDINATION = "coordination"
    RESOURCE_MANAGEMENT = "resource_management"
    STATE_CORRUPTION = "state_corruption"
    TIMEOUT = "timeout"

@dataclass
class ErrorEvent:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    retry_count: int = 0
    
class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker OPEN - service unavailable")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED")
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e

class RetryStrategy:
    """Configurable retry strategy with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_factor = exponential_factor
    
    def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_factor ** attempt),
                        self.max_delay
                    )
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        raise last_exception

class ErrorRecoveryManager:
    """Centralized error recovery and resilience management"""
    
    def __init__(self):
        self.error_history: List[ErrorEvent] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[ErrorCategory, RetryStrategy] = {}
        self.recovery_handlers: Dict[ErrorCategory, Callable] = {}
        self.error_patterns: Dict[str, int] = {}
        self._lock = threading.Lock()
        
        # Initialize default retry strategies
        self._setup_default_strategies()
        self._setup_recovery_handlers()
    
    def _setup_default_strategies(self):
        """Setup default retry strategies for different error categories"""
        self.retry_strategies = {
            ErrorCategory.NETWORK: RetryStrategy(max_retries=3, base_delay=1.0),
            ErrorCategory.LLM_API: RetryStrategy(max_retries=2, base_delay=2.0),
            ErrorCategory.AGENT_LOGIC: RetryStrategy(max_retries=1, base_delay=0.5),
            ErrorCategory.GRID_OPERATION: RetryStrategy(max_retries=2, base_delay=0.1),
            ErrorCategory.COORDINATION: RetryStrategy(max_retries=3, base_delay=1.0),
            ErrorCategory.RESOURCE_MANAGEMENT: RetryStrategy(max_retries=2, base_delay=0.5),
            ErrorCategory.STATE_CORRUPTION: RetryStrategy(max_retries=1, base_delay=5.0),
            ErrorCategory.TIMEOUT: RetryStrategy(max_retries=2, base_delay=1.0)
        }
    
    def _setup_recovery_handlers(self):
        """Setup recovery handlers for different error categories"""
        self.recovery_handlers = {
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.LLM_API: self._recover_llm_error,
            ErrorCategory.AGENT_LOGIC: self._recover_agent_error,
            ErrorCategory.GRID_OPERATION: self._recover_grid_error,
            ErrorCategory.COORDINATION: self._recover_coordination_error,
            ErrorCategory.RESOURCE_MANAGEMENT: self._recover_resource_error,
            ErrorCategory.STATE_CORRUPTION: self._recover_state_corruption,
            ErrorCategory.TIMEOUT: self._recover_timeout_error
        }
    
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    severity: ErrorSeverity, context: Dict[str, Any] = None) -> bool:
        """Handle an error with appropriate recovery strategy"""
        context = context or {}
        
        # Create error event
        error_event = ErrorEvent(
            error_id=f"{category.value}_{int(time.time())}_{id(error)}",
            category=category,
            severity=severity,
            message=str(error),
            context=context,
            stack_trace=traceback.format_exc()
        )
        
        with self._lock:
            self.error_history.append(error_event)
            
            # Track error patterns
            error_pattern = f"{category.value}_{type(error).__name__}"
            self.error_patterns[error_pattern] = self.error_patterns.get(error_pattern, 0) + 1
            
            # Attempt recovery
            recovery_successful = self._attempt_recovery(error_event)
            error_event.recovery_attempted = True
            error_event.recovery_successful = recovery_successful
            
            # Log error
            log_method = self._get_log_method(severity)
            log_method(f"Error handled: {error_event.error_id} - {error_event.message}")
            
            return recovery_successful
    
    def _attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt to recover from an error"""
        try:
            if error_event.category in self.recovery_handlers:
                handler = self.recovery_handlers[error_event.category]
                return handler(error_event)
            else:
                logger.warning(f"No recovery handler for category: {error_event.category}")
                return False
        except Exception as e:
            logger.error(f"Recovery attempt failed: {str(e)}")
            return False
    
    def _recover_network_error(self, error_event: ErrorEvent) -> bool:
        """Recover from network-related errors"""
        logger.info("Attempting network error recovery")
        
        # Simple network recovery - could be enhanced with connectivity checks
        time.sleep(2.0)  # Wait for network to stabilize
        
        # Could add network connectivity tests here
        return True
    
    def _recover_llm_error(self, error_event: ErrorEvent) -> bool:
        """Recover from LLM API errors"""
        logger.info("Attempting LLM API error recovery")
        
        # Check if it's a rate limit error
        if "rate limit" in error_event.message.lower():
            time.sleep(10.0)  # Wait longer for rate limits
            return True
        
        # Check if it's an authentication error
        if "auth" in error_event.message.lower():
            logger.error("Authentication error - manual intervention required")
            return False
        
        # For other LLM errors, short wait and retry
        time.sleep(5.0)
        return True
    
    def _recover_agent_error(self, error_event: ErrorEvent) -> bool:
        """Recover from agent logic errors"""
        logger.info("Attempting agent error recovery")
        
        # Agent errors often require state reset
        agent_id = error_event.context.get("agent_id")
        if agent_id:
            # Could reset agent state here if we had reference to the agent
            logger.info(f"Agent {agent_id} state recovery attempted")
        
        return True
    
    def _recover_grid_error(self, error_event: ErrorEvent) -> bool:
        """Recover from grid operation errors"""
        logger.info("Attempting grid error recovery")
        
        # Grid errors are usually recoverable by retrying
        return True
    
    def _recover_coordination_error(self, error_event: ErrorEvent) -> bool:
        """Recover from coordination errors"""
        logger.info("Attempting coordination error recovery")
        
        # Coordination errors might require message queue reset
        return True
    
    def _recover_resource_error(self, error_event: ErrorEvent) -> bool:
        """Recover from resource management errors"""
        logger.info("Attempting resource error recovery")
        
        # Resource errors might be recoverable by releasing resources
        return True
    
    def _recover_state_corruption(self, error_event: ErrorEvent) -> bool:
        """Recover from state corruption"""
        logger.warning("Attempting state corruption recovery")
        
        # State corruption is serious - might need full reset
        # This would require careful implementation
        return False
    
    def _recover_timeout_error(self, error_event: ErrorEvent) -> bool:
        """Recover from timeout errors"""
        logger.info("Attempting timeout error recovery")
        
        # Timeout errors are usually recoverable by retrying
        return True
    
    def _get_log_method(self, severity: ErrorSeverity):
        """Get appropriate logging method for severity"""
        if severity == ErrorSeverity.CRITICAL:
            return logger.critical
        elif severity == ErrorSeverity.HIGH:
            return logger.error
        elif severity == ErrorSeverity.MEDIUM:
            return logger.warning
        else:
            return logger.info
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns"""
        with self._lock:
            total_errors = len(self.error_history)
            recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour
            
            severity_distribution = {}
            category_distribution = {}
            recovery_rate = 0
            
            for error in self.error_history:
                # Severity distribution
                severity = error.severity.value
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
                
                # Category distribution
                category = error.category.value
                category_distribution[category] = category_distribution.get(category, 0) + 1
                
                # Recovery rate
                if error.recovery_attempted and error.recovery_successful:
                    recovery_rate += 1
            
            if total_errors > 0:
                recovery_rate = recovery_rate / total_errors
            
            return {
                "total_errors": total_errors,
                "recent_errors": len(recent_errors),
                "severity_distribution": severity_distribution,
                "category_distribution": category_distribution,
                "recovery_rate": recovery_rate,
                "error_patterns": dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)),
                "circuit_breaker_states": {name: cb.state for name, cb in self.circuit_breakers.items()}
            }

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator for automatic error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the global error recovery manager
                from app.utils.globals import get_error_recovery_manager
                error_manager = get_error_recovery_manager()
                
                context = {
                    "function_name": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                # Handle the error
                recovery_successful = error_manager.handle_error(e, category, severity, context)
                
                if not recovery_successful and severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                    raise e
                
                # Return a safe default value based on function name/return type
                return _get_safe_default(func, e)
                
        return wrapper
    return decorator

def _get_safe_default(func: Callable, error: Exception) -> Any:
    """Get a safe default return value for a function that failed"""
    func_name = func.__name__.lower()
    
    # Common return patterns
    if 'step' in func_name or 'execute' in func_name:
        return None
    elif 'get' in func_name and 'list' in func_name:
        return []
    elif 'get' in func_name and any(word in func_name for word in ['dict', 'map', 'status']):
        return {}
    elif 'is_' in func_name or 'can_' in func_name or 'has_' in func_name:
        return False
    elif 'count' in func_name or 'size' in func_name or 'length' in func_name:
        return 0
    else:
        return None

# Context manager for error handling
@contextmanager
def error_context(category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                  context: Dict[str, Any] = None):
    """Context manager for handling errors in a block of code"""
    try:
        yield
    except Exception as e:
        from app.utils.globals import get_error_recovery_manager
        error_manager = get_error_recovery_manager()
        
        error_manager.handle_error(e, category, severity, context or {})
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            raise

# Timeout decorator
def timeout(seconds: float):
    """Decorator to add timeout to function calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set up the timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Cancel the alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

# Async timeout function
async def async_timeout(coro, seconds: float):
    """Add timeout to async coroutine"""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Async operation timed out after {seconds} seconds")

class HealthChecker:
    """System health monitoring and checks"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, Dict] = {}
        self.check_intervals: Dict[str, float] = {}
        self.last_check_times: Dict[str, float] = {}
    
    def register_check(self, name: str, check_func: Callable, interval: float = 60.0):
        """Register a health check function"""
        self.checks[name] = check_func
        self.check_intervals[name] = interval
        self.last_check_times[name] = 0
        logger.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {"status": "error", "message": f"Check {name} not found"}
        
        try:
            start_time = time.time()
            result = self.checks[name]()
            execution_time = time.time() - start_time
            
            check_result = {
                "status": "healthy" if result else "unhealthy",
                "execution_time": execution_time,
                "timestamp": time.time(),
                "details": result if isinstance(result, dict) else {"result": result}
            }
            
            self.last_check_results[name] = check_result
            self.last_check_times[name] = time.time()
            
            return check_result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "timestamp": time.time(),
                "execution_time": 0
            }
            self.last_check_results[name] = error_result
            return error_result
    
    def run_all_checks(self) -> Dict[str, Dict]:
        """Run all registered health checks"""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
    
    def run_due_checks(self) -> Dict[str, Dict]:
        """Run health checks that are due based on their intervals"""
        results = {}
        current_time = time.time()
        
        for name, interval in self.check_intervals.items():
            if current_time - self.last_check_times[name] >= interval:
                results[name] = self.run_check(name)
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.last_check_results:
            return {"status": "unknown", "message": "No health checks run yet"}
        
        healthy_checks = 0
        total_checks = len(self.last_check_results)
        
        for result in self.last_check_results.values():
            if result["status"] == "healthy":
                healthy_checks += 1
        
        if healthy_checks == total_checks:
            overall_status = "healthy"
        elif healthy_checks > total_checks / 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "healthy_checks": healthy_checks,
            "total_checks": total_checks,
            "health_percentage": (healthy_checks / total_checks) * 100,
            "last_updated": max(r["timestamp"] for r in self.last_check_results.values()),
            "check_details": self.last_check_results
        }

# Performance monitoring decorator
def monitor_performance(track_memory: bool = False):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import os
            
            start_time = time.time()
            start_memory = None
            
            if track_memory:
                process = psutil.Process(os.getpid())
                start_memory = process.memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                
                # Record successful execution
                execution_time = time.time() - start_time
                
                performance_data = {
                    "function_name": func.__name__,
                    "execution_time": execution_time,
                    "success": True,
                    "timestamp": time.time()
                }
                
                if track_memory and start_memory:
                    end_memory = process.memory_info().rss
                    performance_data["memory_delta"] = end_memory - start_memory
                
                # Log performance data
                if execution_time > 5.0:  # Log slow operations
                    logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}s")
                
                from app.utils.globals import get_performance_tracker
                tracker = get_performance_tracker()
                if tracker:
                    tracker.record_performance(performance_data)
                
                return result
                
            except Exception as e:
                # Record failed execution
                execution_time = time.time() - start_time
                
                performance_data = {
                    "function_name": func.__name__,
                    "execution_time": execution_time,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
                
                from app.utils.globals import get_performance_tracker
                tracker = get_performance_tracker()
                if tracker:
                    tracker.record_performance(performance_data)
                
                raise
        
        return wrapper
    return decorator

class PerformanceTracker:
    """Track and analyze performance metrics"""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.performance_data: List[Dict] = []
        self.function_stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def record_performance(self, data: Dict):
        """Record performance data"""
        with self._lock:
            self.performance_data.append(data)
            
            # Maintain size limit
            if len(self.performance_data) > self.max_entries:
                self.performance_data = self.performance_data[-self.max_entries:]
            
            # Update function statistics
            func_name = data["function_name"]
            if func_name not in self.function_stats:
                self.function_stats[func_name] = {
                    "call_count": 0,
                    "success_count": 0,
                    "total_time": 0.0,
                    "min_time": float('inf'),
                    "max_time": 0.0,
                    "avg_time": 0.0
                }
            
            stats = self.function_stats[func_name]
            stats["call_count"] += 1
            
            if data["success"]:
                stats["success_count"] += 1
            
            exec_time = data["execution_time"]
            stats["total_time"] += exec_time
            stats["min_time"] = min(stats["min_time"], exec_time)
            stats["max_time"] = max(stats["max_time"], exec_time)
            stats["avg_time"] = stats["total_time"] / stats["call_count"]
    
    def get_function_stats(self, func_name: str = None) -> Dict:
        """Get performance statistics for a function or all functions"""
        with self._lock:
            if func_name:
                return self.function_stats.get(func_name, {})
            else:
                return self.function_stats.copy()
    
    def get_slow_operations(self, threshold: float = 1.0) -> List[Dict]:
        """Get operations that took longer than threshold"""
        with self._lock:
            return [
                data for data in self.performance_data
                if data["execution_time"] > threshold
            ]
    
    def get_recent_performance(self, minutes: int = 10) -> List[Dict]:
        """Get performance data from recent minutes"""
        cutoff_time = time.time() - (minutes * 60)
        with self._lock:
            return [
                data for data in self.performance_data
                if data["timestamp"] > cutoff_time
            ]

# Global instances (to be initialized in main application)
_error_recovery_manager = None
_health_checker = None
_performance_tracker = None

def initialize_error_handling():
    """Initialize global error handling components"""
    global _error_recovery_manager, _health_checker, _performance_tracker
    
    _error_recovery_manager = ErrorRecoveryManager()
    _health_checker = HealthChecker()
    _performance_tracker = PerformanceTracker()
    
    # Register default health checks
    _register_default_health_checks()
    
    logger.info("Error handling and resilience system initialized")

def _register_default_health_checks():
    """Register default system health checks"""
    import psutil
    import os
    
    def memory_check():
        """Check system memory usage"""
        memory = psutil.virtual_memory()
        return {
            "status": "healthy" if memory.percent < 80 else "unhealthy",
            "memory_percent": memory.percent,
            "available_gb": memory.available / (1024**3)
        }
    
    def disk_check():
        """Check disk space"""
        disk = psutil.disk_usage('/')
        return {
            "status": "healthy" if disk.percent < 90 else "unhealthy",
            "disk_percent": disk.percent,
            "free_gb": disk.free / (1024**3)
        }
    
    def process_check():
        """Check current process health"""
        process = psutil.Process(os.getpid())
        return {
            "status": "healthy",
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / (1024**2),
            "threads": process.num_threads()
        }
    
    _health_checker.register_check("memory", memory_check, interval=30.0)
    _health_checker.register_check("disk", disk_check, interval=60.0)
    _health_checker.register_check("process", process_check, interval=30.0)

def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager"""
    if _error_recovery_manager is None:
        initialize_error_handling()
    return _error_recovery_manager

def get_health_checker() -> HealthChecker:
    """Get the global health checker"""
    if _health_checker is None:
        initialize_error_handling()
    return _health_checker

def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker"""
    if _performance_tracker is None:
        initialize_error_handling()
    return _performance_tracker