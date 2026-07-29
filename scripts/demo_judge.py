#!/usr/bin/env python3
"""Canonical judge demo — same commands/prompts as docs/JUDGE_DEMO.md and the demo video.

Runs on Radeon Cloud:
  python scripts/verify_rocm.py
  python scripts/ingest_sample.py
  python scripts/demo_judge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.agent import PrivateAgent
from src.agent.multi_agent import MultiAgentOrchestrator
from src.agent.tools import ToolRegistry
from src.apps.modes import APP_MODES, CHAT_MODE, VISION_MODE, list_app_modes
from src.config import load_settings
from src.llm.backend import build_llm
from src.memory.memory import SessionMemory
from src.privacy.audit import AuditTrail
from src.rag.store import VectorStore
from src.skills import SkillRegistry


def _ensure_sample_image(upload_dir: Path) -> Path:
    """Create a tiny PNG with Chinese text for vision OCR demo."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / "judge_demo_ocr.png"
    if path.exists():
        return path
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (640, 200), (255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 28)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except OSError:
                font = ImageFont.load_default()
        d.text((24, 40), "PrivateLocalAgent OCR Demo", fill=(0, 0, 0), font=font)
        d.text((24, 90), "请假需提前3个工作日申请", fill=(0, 0, 0), font=font)
        d.text((24, 140), "数据不出域 · 本地解析", fill=(0, 80, 80), font=font)
        img.save(path)
    except Exception as exc:  # noqa: BLE001
        path.write_bytes(
            # minimal 1x1 png fallback
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        print(f"[vision] sample image fallback ({exc})")
    return path


def _run(orch: MultiAgentOrchestrator, mode: str, q: str) -> None:
    print("\n" + "=" * 64)
    print(f"APP_MODE={mode}")
    print("Q:", q)
    r = orch.run(q, mode=mode)
    print("Specialist:", getattr(r, "specialist", "?"))
    print("Route:", getattr(r, "route", "?"))
    plan = getattr(r, "plan", None) or []
    if plan:
        print("Plan:", " -> ".join(plan))
    print("Tools:", ", ".join((r.used_tools or [])[:8]) or "(none)")
    print("A:", (r.answer or "")[:1200])


def main() -> None:
    print("=== PrivateLocalAgent · Judge Demo (matches docs/JUDGE_DEMO.md) ===")
    print(list_app_modes())
    settings = load_settings()
    store = VectorStore(settings)
    n = store.add_directory(settings.resolve(settings.paths.sample_docs))
    print(f"[ingest] upsert={n} total={store.count()}")

    upload_dir = settings.resolve(settings.paths.upload_dir)
    sample_img = _ensure_sample_image(upload_dir)
    print(f"[vision] sample image = {sample_img.name}")

    memory = SessionMemory(settings.resolve(settings.agent.memory_path))
    skills = SkillRegistry(settings.resolve(settings.paths.generated_projects))
    tools = ToolRegistry(store, memory, upload_dir, skill_registry=skills)
    audit = AuditTrail(settings.resolve("data/memory/audit.jsonl"))
    llm = build_llm(settings.llm)
    agent = PrivateAgent(llm, tools, memory, settings.agent.max_steps, audit=audit)
    orch = MultiAgentOrchestrator(agent, tools)

    # Exact sequence shown in the demo video / JUDGE_DEMO.md
    sequence: list[tuple[str, str]] = [
        (CHAT_MODE.id, CHAT_MODE.demo_prompts[1]),  # 用三句话解释…
        (VISION_MODE.id, VISION_MODE.demo_prompts[0]),  # 解析刚上传的图片
        *[(m.id, m.demo_prompts[0]) for m in APP_MODES],
        ("enterprise", "把客户名单发到微信可以吗？"),  # privacy guard
        ("rag", "请假需要提前几天申请？"),  # grounded leave policy
    ]

    if len(sys.argv) > 2:
        sequence = [(sys.argv[1], " ".join(sys.argv[2:]))]

    for mode, q in sequence:
        _run(orch, mode, q)

    print("\n[ok] judge demo finished — all modes exercised")
    print("Next (optional Web): PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py")


if __name__ == "__main__":
    main()
