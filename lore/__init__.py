"""lore: compile the fleet's incident history into living runbooks per failure class."""

__version__ = "0.1.2"

from lore.classes import UNCLASSIFIED_ID, ClassRegistry, FailureClass, get_registry

__all__ = [
    "UNCLASSIFIED_ID",
    "ClassRegistry",
    "FailureClass",
    "__version__",
    "get_registry",
]
