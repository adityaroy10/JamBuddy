from .interface import AccompanimentInterface, ChordEvent
from .rule_based import RuleBasedAccompaniment

__all__ = ["AccompanimentInterface", "RuleBasedAccompaniment", "RealJamAccompaniment"]

try:
    from .realjam_adapter import RealJamAccompaniment
except ImportError:
    RealJamAccompaniment = None  # type: ignore
