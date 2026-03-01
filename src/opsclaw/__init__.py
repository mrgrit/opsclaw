"""OpsClaw MVP scaffold package."""

from .models import TaskRequest, TaskResult
from .orchestrator import ManagerOrchestrator

__all__ = ["TaskRequest", "TaskResult", "ManagerOrchestrator"]
