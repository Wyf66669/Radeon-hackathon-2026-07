"""Notebook visual launcher: in-page UI + external web page.

Avoids broken ipywidgets. Starts Doubao-style web_http_demo, opens a Cloudflare
quick tunnel when possible, and embeds that HTTPS URL in an iframe so it works
inside remote JupyterLab (where /proxy/<port> is often 404).
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import threading
import time
from html import escape
from pathlib import Path
from typing import Any, Callable

from src.apps.judge_script import JUDGE_SEQUENCE, prompts_for_mode
from src.apps.modes import UI_MODES

_EMBED_SERVERS: dict[int, Any] = {}
_TUNNEL_PROCS: dict[int, subprocess.Popen] = {}
_TUNNEL_URLS: dict[int, str] = {}


def render_shell(history: list[dict[str, Any]], subtitle: str = "本地私有 Agent") -> str:
    css = (
        "<style>.pla-shell{font-family:Segoe UI,PingFang SC,sans-serif;max-width:920px;"
        "margin:0 auto;padding:16px;border-radius:16px;color:#e5e7eb;background:#0f172a;"
        "border:1px solid #334155}.pla-brand{font-size:24px;font-weight:700}"
        ".pla-chat{min-height:160px;max-height:420px;overflow:auto;padding:10px}"
        ".pla-row{display:flex;margin:8px 0}.pla-row.user{justify-content:flex-end}"
        ".pla-bubble{max-width:86%;padding:10px 12px;border-radius:12px;white-space:pre-wrap}"
        ".pla-bubble.user{background:#14b8a6;color:#042f2e}.pla-bubble.bot{background:#1f2937}</style>"
    )
    if not history:
        body = "<div style='color:#64748b;text-align:center;padding:24px'>在下方页面上传图片并对话</div>"
    else:
        parts = []
        for turn in history:
            parts.append(
                f"<div class='pla-row user'><div class='pla-bubble user'>{escape(str(turn.get('q','')))}</div></div>"
            )
            parts.append(
                f"<div class='pla-row bot'><div class='pla-bubble bot'>{escape(str(turn.get('a','')))}</div></div>"
            )
        body = "".join(parts)
    return (
        f"{css}<div class='pla-shell'><div class='pla-brand'>PrivateLocalAgent</div>"
        f"<div style='color:#94a3b8;margin:4px 0 10px'>{escape(subtitle)}</div>"
        f"<div class='pla-chat'>{body}</div></div>"
    )


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


def _load_web_module() -> Any:
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    demo_path = root / "scripts" / "web_http_demo.py"
    spec = importlib.util.spec_from_file_location("pla_web_http_demo", demo_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {demo_path}")
    web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web)
    return web


def _start_web_for_orch(orch: Any, default_mode: str = "chat") -> tuple[Any, int]:
    web = _load_web_module()
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
    if port not in _EMBED_SERVERS:
        # Bind localhost; Cloudflare tunnel exposes it publicly for iframe + external tab.
        server = web.ThreadingHTTPServer(("127.0.0.1", port), web.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _EMBED_SERVERS[port] = server
    return web, port


def _ensure_cloudflared() -> str | None:
    existing = shutil.which("cloudflared")
    if existing:
        return existing
    for p in ("/usr/local/bin/cloudflared", "/usr/bin/cloudflared"):
        if Path(p).exists():
            return p
    root = Path(__file__).resolve().parents[2]
    target = root / ".tools" / "cloudflared"
    if target.exists() and target.stat().st_size > 1_000_000:
        target.chmod(target.stat().st_mode | 0o111)
        return str(target)
    try:
        from scripts.run_cloudflare_tunnel import ensure_cloudflared

        return ensure_cloudflared()
    except Exception as exc:  # noqa: BLE001
        print(f"[ui] cloudflared unavailable: {exc}", flush=True)
        return None


def _start_tunnel(port: int) -> str | None:
    if port in _TUNNEL_URLS:
        return _TUNNEL_URLS[port]
    bin_path = _ensure_cloudflared()
    if not bin_path:
        return None
    try:
        proc = subprocess.Popen(
            [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ui] tunnel start failed: {exc}", flush=True)
        return None
    _TUNNEL_PROCS[port] = proc
    url = None
    deadline = time.time() + 45
    assert proc.stdout is not None
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if not line:
            time.sleep(0.2)
            continue
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            url = m.group(0)
            break
    if url:
        _TUNNEL_URLS[port] = url
        print(f"[ui] public={url}", flush=True)
    else:
        print("[ui] tunnel URL not ready; iframe may need proxy/public link", flush=True)
    return url


class NotebookVisualChat:
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
        self.local_url: str | None = None
        self.proxy_url: str | None = None
        self.public_url: str | None = None
        if upload_dir:
            self.upload_dir = Path(upload_dir)
        else:
            tools = getattr(runner, "tools", None)
            ud = getattr(tools, "upload_dir", None)
            self.upload_dir = Path(ud) if ud else Path("data/uploads")
            if not self.upload_dir.is_absolute():
                from src.config import load_settings

                self.upload_dir = load_settings().resolve("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> Path:
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
        from IPython.display import HTML, clear_output, display

        _web, port = _start_web_for_orch(self.runner, self.mode)
        self.port = port
        self.local_url = f"http://127.0.0.1:{port}/"
        self.proxy_url = _jupyter_proxy_url(port)
        # Public HTTPS URL embeds correctly inside remote Jupyter (proxy often 404).
        self.public_url = _start_tunnel(port)

        embed_src = self.public_url or self.proxy_url
        external = self.public_url or self.proxy_url or self.local_url

        clear_output(wait=True)
        display(
            HTML(
                f"""
<div style="font-family:Segoe UI,PingFang SC,Microsoft YaHei,sans-serif;color:#e5e7eb">
  <div style="padding:12px 14px;border-radius:12px;background:#0f172a;border:1px solid #334155;margin-bottom:10px">
    <b style="color:#99f6e4">PrivateLocalAgent</b>
    · Notebook 内嵌页面 + 外部页面（含上传）
    <div style="margin-top:8px;font-size:13px;line-height:1.7">
      <a href="{escape(external)}" target="_blank" rel="noopener" style="color:#5eead4">打开外部完整界面</a>
      &nbsp;|&nbsp; 本机 <code style="color:#fbbf24">{escape(self.local_url)}</code>
      {("&nbsp;|&nbsp; proxy <code>" + escape(self.proxy_url) + "</code>") if self.proxy_url else ""}
    </div>
  </div>
  <iframe src="{escape(embed_src)}" title="PrivateLocalAgent"
    style="width:100%;height:780px;border:1px solid #334155;border-radius:14px;background:#0b1220"></iframe>
</div>
"""
            )
        )
        print(f"[ui] local={self.local_url}", flush=True)
        print(f"[ui] proxy={self.proxy_url}", flush=True)
        print(f"[ui] public={self.public_url}", flush=True)
        print(f"[ui] embed={embed_src}", flush=True)


def launch_notebook_visual(
    runner: Any,
    plan_fn: Callable[[str], list[str]] | None = None,
    default_mode: str = "chat",
    upload_dir: Path | str | None = None,
) -> NotebookVisualChat:
    ui = NotebookVisualChat(
        runner,
        plan_fn=plan_fn,
        default_mode=default_mode,
        upload_dir=upload_dir,
    )
    ui.show()
    return ui
