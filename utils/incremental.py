from pathlib import Path
from typing import Set


class IncrementalStore:
    """Simple file-backed store to track processed URLs for incremental scraping."""

    def __init__(self, filepath: str):
        self.path = Path(filepath)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: Set[str] = set()
        if self.path.exists():
            for line in self.path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    self._seen.add(line.strip())

    def has(self, url: str) -> bool:
        return url in self._seen

    def add(self, url: str):
        if url not in self._seen:
            self._seen.add(url)
            with self.path.open('a', encoding='utf-8') as f:
                f.write(url + "\n")

    def all(self):
        return set(self._seen)
