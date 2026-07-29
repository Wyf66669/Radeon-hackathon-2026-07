"""Notebook visual launcher: embed Doubao-style web UI (no ipywidgets).

Radeon Cloud Jupyter often breaks with "Error displaying widget: model not found".
This module starts the existing web_http_demo server against a ready orchestrator
and shows it in an iframe via Jupyter's /proxy/<port>/ (or a clickable link).
"""

from __future__ import annotations

import os
import socket
import threading
from html import escape
from pathlib import Path
from typing import Any, Callable

from src.apps.judge_script import JUDGE_SEQUENCE, prompts_for_mode
from src.apps.modes import UI_MODES

# Keep HTML helpers for ask()/fallback
CSS = """
<style>
.pla-shell {
  font-family: "IBM Plex Sans", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 920px; margin: 0 auto; padding: 18px 16px 28px; border-radius: 18px;
  color: #e5e7eb;
  background:
    radial-gradient(900px 380px at 8% -20%, rgba(20,184,166,.22), transparent 55%),
    #0f172a;
  border: 1px solid #334155;
}
.pla-brand { font-size: 28px; font-weight: 750; margin: 0 0 4px; color: #f8fafc; }
.pla-sub { margin: 0 0 16px; color: #94a3b8; font-size: 14px; }
.pla-chat {
  min-height: 180px; max-height: 420px; overflow-y: auto; padding: 12px;
  border-radius: 14px; background: rgba(15,23,42,.65); border: 1px solid #1f2937;
}
.pla-empty { color: #64748b; text-align: center; padding: 36px 12px; font-size: 14px; }
.pla-row { display: flex; margin: 8px 0; }
.pla-row.user { justify-content: flex-end; }
.pla-bubble { max-width: 86%; padding: 12px 14px; border-radius: 14px; white-space: pre-wrap; font-size: 14px; }
.pla-bubble.user { background: #14b8a6; color: #042f2e; font-weight: 600; }
.pla-bubble.bot { background: #1f2937; color: #e5e7eb; border: 1px solid #334155; }
</style>
"""

_EMBED_SERVERS: dict[int, Any] = {}


def render_shell(history: list[dict[str, Any]], subtitle: str = "本地私有 Agent") -> str:
    if not history:
        body = '<div class="pla-empty">下方嵌入网页可上传图片并对话</div>'
    else:
        parts = []
        for turn in history:
            parts.append(
                f'<div class="pla-row user"><div class="pla-bubble user">{escape(str(turn.get("q","")))}</div></div>'
            )
            parts.append(
                f'<div class="pla-row bot"><div class="pla-bubble bot">{escape(str(turn.get("a","")))}</div></div>'
            )
        body = "\n".join(parts)
    return f'{CSS}<div class="pla-shell"><div class="pla-brand">PrivateLocalAgent</div><p class="pla-sub">{escape(subtitle)}</p><div class="pla-chat">{body}</div></div>'


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _jupyter_proxy_url(port: int) -> str:
    prefix = (
        os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
        or os.environ.get("NB_PREFIX")
        or ""
    ).rstrip("/")
    if prefix:
        return f"{prefix}/proxy/{port}/"
    return f"/proxy/{port}/"


def _start_web_for_orch(orch: Any, default_mode: str = "chat") -> int:
    """Bind web_http_demo to an already-built orchestrator; return port."""
    import importlib.util
    import sys
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    demo_path = root / "scripts" / "web_http_demo.py"
    spec = importlib.util.spec_from_file_location("pla_web_http_demo", demo_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {demo_path}")
    web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web)

    upload_dir = getattr(getattr(orch, "tools", None), "upload_dir", None)
    if upload_dir is None:
        from src.config import load_settings

        upload_dir = load_settings().resolve("data/uploads")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    web.ORCH = orch
    web.UPLOAD_DIR = Path(upload_dir)
    web.READY = True
    web.LOADING = False
    web.LOAD_ERROR = ""
    web.MODE = default_mode if default_mode in {m.id for m in UI_MODES} else "chat"
    web._new_session(web.MODE)

    port = int(os.getenv("PLA_NOTEBOOK_UI_PORT", "0") or 0) or _free_port()
    if port in _EMBED_SERVERS:
        return port

    server = web.ThreadingHTTPServer(("127.0.0.1", port), web.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _EMBED_SERVERS[port] = server
    return port


class NotebookVisualChat:
    """Thin wrapper kept for ask()/upload helpers + embedded web UI handle."""

    def __init__(
        self,
        runner: Any,
        plan_fn: Callable[[str], list[str]] | None = None,
        default_mode: str = "chat",
        upload_dir: Path | str | None = None,
    ) -> None:
        self.runner = runner
        self.plan_fn = plan_fn
        self.mode = default_mode
        self.history: list[dict[str, Any]] = []
        self.last_image: str | None = None
        self.port: int | None = None
        self.proxy_url: str | None = None
        if upload_dir:
            self.upload_dir = Path(upload_dir)
        else:
            tools = getattr(runner, "tools", None)
            ud = getattr(tools, "upload_dir", None)
            if ud:
                self.upload_dir = Path(ud)
            else:
                from src.config import load_settings

                self.upload_dir = load_settings().resolve("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> Path:
        import re

        name = Path(filename or "upload.png").name
        name = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
        if Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            name = f"{Path(name).stem or 'upload'}.png"
        target = self.upload_dir / name[:120]
        target.write_bytes(content)
        self.last_image = target.name
        return target

    def upload_path(self, path: str | Path) -> str:
        src = Path(str(path).strip().strip('"').strip("'"))
        if not src.is_file():
            cand = self.upload_dir / src.name
            if not cand.is_file():
                raise FileNotFoundError(f"找不到图片: {path}")
            src = cand
        return self.save_upload(src.name, src.read_bytes()).name

    def _suggestions(self) -> list[str]:
        primary = prompts_for_mode(self.mode)
        return primary or [q for _, q in JUDGE_SEQUENCE[:5]]

    def _run(self, query: str) -> dict[str, Any]:
        query = (query or "").strip()
        if not query:
            raise ValueError("问题不能为空")
        result = self.runner.run(query, mode=self.mode)
        turn = {
            "q": query,
            "a": getattr(result, "answer", str(result)),
            "tools": list(getattr(result, "used_tools", None) or []),
            "mode": getattr(result, "app_mode", None) or self.mode,
        }
        self.history.append(turn)
        return turn

    def ask(self, query: str, mode: str | None = None) -> str:
        from IPython.display import HTML, clear_output, display

        if mode:
            self.mode = mode
        clear_output(wait=True)
        display(HTML(render_shell(self.history, subtitle="处理中…")))
        turn = self._run(query)
        clear_output(wait=True)
        display(HTML(render_shell(self.history)))
        return str(turn.get("a", ""))

    def show(self, use_widgets: bool | None = None) -> None:  # noqa: ARG002
        """Always embed web UI — avoids ipywidgets 'model not found'."""
        from IPython.display import HTML, clear_output, display

        port = _start_web_for_orch(self.runner, self.mode)
        self.port = port
        proxy = _jupyter_proxy_url(port)
        self.proxy_url = proxy
        local = f"http://127.0.0.1:{port}/"
        clear_output(wait=True)
        display(
            HTML(
                f"""
<div style="font-family:Segoe UI,PingFang SC,sans-serif;margin:8px 0 12px;color:#e5e7eb">
  <div style="padding:12px 14px;border-radius:12px;background:#0f172a;border:1px solid #334155">
    <b style="color:#99f6e4">PrivateLocalAgent</b>
    · 已绕过 ipywidgets（避免 model not found）· 支持上传图片<br/>
    <a href="{escape(proxy)}" target="_blank" rel="noopener"
       style="color:#5eead4">打开完整界面</a>
    &nbsp;|&nbsp; 本机直连 <code style="color:#fbbf24">{escape(local)}</code>
  </div>
  <iframe src="{escape(proxy)}" title="PrivateLocalAgent"
    style="width:100%;height:760px;margin-top:10px;border:1px solid #334155;
           border-radius:14px;background:#0b1220"></iframe>
</div>
"""
            )
        )
        print(f"[ui] proxy={proxy}", flush=True)
        print(f"[ui] local={local}", flush=True)


def launch_notebook_visual(
    runner: Any,
    plan_fn: Callable[[str], list[str]] | None = None,
    default_mode: str = "chat",
    upload_dir: Path | str | None = None,
) -> NotebookVisualChat:
    """Launch embedded web UI for Notebook (upload + chat). No ipywidgets."""
    ui = NotebookVisualChat(
        runner,
        plan_fn=plan_fn,
        default_mode=default_mode,
        upload_dir=upload_dir,
    )
    ui.show()
    return ui
