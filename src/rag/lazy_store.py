"""Lazy VectorStore — chat/UI can start before KB embedder finishes."""

from __future__ import annotations

import threading
from typing import Any


class LazyVectorStore:
    def __init__(self, settings: Any) -> None:
        self._settings = settings
        self._inner = None
        self._lock = threading.Lock()

    def _get(self):
        if self._inner is not None:
            return self._inner
        with self._lock:
            if self._inner is not None:
                return self._inner
            from src.rag.store import VectorStore

            print("[boot] loading knowledge base embedder (first use)...", flush=True)
            store = VectorStore(self._settings)
            sample = self._settings.resolve(self._settings.paths.sample_docs)
            store.ensure_sample_docs(sample)
            self._inner = store
            print("[boot] knowledge base ready", flush=True)
            return self._inner

    def warm(self) -> None:
        try:
            self._get()
        except Exception as exc:  # noqa: BLE001
            print(f"[boot] kb warm failed: {exc}", flush=True)

    def search(self, *args, **kwargs):
        return self._get().search(*args, **kwargs)

    def count(self) -> int:
        return self._get().count()

    def add_directory(self, *args, **kwargs):
        return self._get().add_directory(*args, **kwargs)

    def add_file(self, *args, **kwargs):
        return self._get().add_file(*args, **kwargs)
