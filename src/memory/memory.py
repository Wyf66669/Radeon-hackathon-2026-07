from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionMemory:
    """Lightweight local memory for private agent sessions."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {"notes": [], "facts": [], "history": []}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_note(self, note: str) -> str:
        item = {"ts": datetime.now().isoformat(timespec="seconds"), "note": note}
        self._data.setdefault("notes", []).append(item)
        self.save()
        return f"Saved note ({len(self._data['notes'])} total)."

    def add_fact(self, fact: str) -> str:
        item = {"ts": datetime.now().isoformat(timespec="seconds"), "fact": fact}
        self._data.setdefault("facts", []).append(item)
        self.save()
        return f"Saved fact ({len(self._data['facts'])} total)."

    def recall(self, limit: int = 8) -> str:
        notes = self._data.get("notes", [])[-limit:]
        facts = self._data.get("facts", [])[-limit:]
        lines = ["## Facts"]
        lines += [f"- {x['fact']}" for x in facts] or ["- (none)"]
        lines.append("## Notes")
        lines += [f"- {x['note']}" for x in notes] or ["- (none)"]
        return "\n".join(lines)

    def append_history(self, role: str, content: str) -> None:
        self._data.setdefault("history", []).append(
            {"ts": datetime.now().isoformat(timespec="seconds"), "role": role, "content": content}
        )
        # Keep history bounded for privacy / disk size
        self._data["history"] = self._data["history"][-100:]
        self.save()

    def recent_turns(self, limit: int = 8) -> list[dict[str, str]]:
        rows = self._data.get("history", [])[-limit:]
        return [{"role": str(x.get("role", "")), "content": str(x.get("content", ""))} for x in rows]

    def format_dialogue(self, limit: int = 8) -> str:
        turns = self.recent_turns(limit)
        if not turns:
            return "(no prior dialogue)"
        lines: list[str] = []
        for t in turns:
            role = "User" if t["role"] == "user" else "Assistant"
            lines.append(f"{role}: {t['content']}")
        return "\n".join(lines)
