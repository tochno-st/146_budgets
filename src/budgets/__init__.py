from .config import Config
from .api import BudgetAPI
from .normalizer import DataNormalizer
from .storage import StorageManager
from .income import IncomeLoader
from .expense import ExpenseLoader

__version__ = "0.1.0"
__all__ = [
    "Config",
    "BudgetAPI",
    "DataNormalizer",
    "StorageManager",
    "IncomeLoader",
    "ExpenseLoader",
]


def get_updater():
    """Lazy import of BudgetUpdater to avoid circular import issues"""
    from .main import BudgetUpdater
    return BudgetUpdater

