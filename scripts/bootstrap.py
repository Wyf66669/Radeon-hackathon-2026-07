#!/usr/bin/env python3
"""One-shot bootstrap for Radeon Cloud / local Windows."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> None:
    run([sys.executable, "-m", "pip", "install", "-U", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    env = ROOT / ".env"
    if not env.exists():
        env.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example")

    # Prefer local GPU backend when available
    try:
        import torch

        gpu = torch.cuda.is_available()
        print(f"torch.cuda.is_available() = {gpu}")
        cfg = ROOT / "configs" / "default.yaml"
        text = cfg.read_text(encoding="utf-8")
        if gpu:
            text = re.sub(r'backend:\s*".*?"', 'backend: "local_transformers"', text, count=1)
            cfg.write_text(text, encoding="utf-8")
            print("Switched llm.backend -> local_transformers")
    except Exception as exc:  # noqa: BLE001
        print(f"GPU probe skipped: {exc}")

    run([sys.executable, str(ROOT / "scripts" / "verify_rocm.py")])
    run([sys.executable, str(ROOT / "scripts" / "ingest_sample.py")])
    print("Bootstrap done. Start demo with: python app.py")


if __name__ == "__main__":
    main()
