from .dependencies import CACHE, call_resolved, depends

__version__ = "1.2.8"

cached = CACHE.cached

__all__ = ["__version__", "depends", "CACHE", "cached", "call_resolved"]
