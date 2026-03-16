"""LunaClaw Brief — Base Source Adapter

Abstract base class for all data source adapters (数据源基类).
All sources must implement the async fetch() method.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from brief.models import Item


class BaseSource(ABC):
    """Base class for all data source adapters (所有数据源适配器的基类)."""

    name: str = "unknown"

    def __init__(self, global_config: dict):
        """Initialize with global config; proxy is set if enabled in config."""
        self.global_config = global_config
        self.proxy = None
        proxy_cfg = global_config.get("proxy", {})
        if proxy_cfg.get("enabled"):
            self.proxy = proxy_cfg.get("http")

    @abstractmethod
    async def fetch(self, since: datetime, until: datetime) -> list[Item]:
        """Fetch items from the source within the given time range (从指定时间范围内拉取条目)."""
        ...
