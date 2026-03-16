"""LunaClaw Brief — Historical deduplication and issue number management.

JSON-based store for tracking previously used items and managing issue counters,
preventing content repetition across report issues.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from brief.models import Item


class UsedItemStore:
    """JSON-based index of historically used content."""

    def __init__(self, path: Path):
        self.path = path
        self._data: dict = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def filter_unseen(self, items: list[Item], window_days: int) -> list[Item]:
        """Filter out items used within the given window_days."""
        cutoff = (datetime.now() - timedelta(days=window_days)).isoformat()
        result: list[Item] = []
        for item in items:
            record = self._data.get(item.item_id)
            if record is None or record.get("used_at", "") < cutoff:
                result.append(item)
        return result

    def mark_used(self, items: list[Item], issue_number: int):
        """Record the currently used items into history."""
        now = datetime.now().isoformat()
        for item in items:
            self._data[item.item_id] = {
                "title": item.title[:80],
                "source": item.source,
                "used_at": now,
                "issue_number": issue_number,
            }
        self._save()


class IssueCounter:
    """Thread-safe issue number counter."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / "issue_counter.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def next(self) -> int:
        data: dict = {}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                data = {}
        current = data.get("counter", 0)
        data["counter"] = current + 1
        data["updated_at"] = datetime.now().isoformat()
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return current + 1

    def peek(self) -> int:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return data.get("counter", 0)
            except (json.JSONDecodeError, IOError):
                pass
        return 0
