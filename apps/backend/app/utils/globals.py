# apps/backend/app/utils/globals.py

"""
Global utilities and singleton instances for the application.
This module provides access to shared components like error handling,
performance tracking, and health monitoring.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global instances
_error_recovery_manager = None
_health_checker = None
_performance_tracker = None

def get_error_recovery_manager():
    """Get the global error recovery manager instance"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        from app.utils.error_handling import ErrorRecoveryManager
        _error_recovery_manager = ErrorRecoveryManager()
        logger.info("Error recovery manager initialized")
    return _error_recovery_manager

def get_health_checker():
    """Get the global health checker instance"""
    global _health_checker
    if _health_checker is None:
        from app.utils.error_handling import HealthChecker
        _health_checker = HealthChecker()
        logger.info("Health checker initialized")
    return _health_checker

def get_performance_tracker():
    """Get the global performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        from app.utils.error_handling import PerformanceTracker
        _performance_tracker = PerformanceTracker()
        logger.info("Performance tracker initialized")
    return _performance_tracker

def initialize_all_systems():
    """Initialize all global systems"""
    get_error_recovery_manager()
    get_health_checker()
    get_performance_tracker()
    logger.info("All global systems initialized")

def cleanup_all_systems():
    """Cleanup all global systems"""
    global _error_recovery_manager, _health_checker, _performance_tracker
    _error_recovery_manager = None
    _health_checker = None
    _performance_tracker = None
    logger.info("All global systems cleaned up")