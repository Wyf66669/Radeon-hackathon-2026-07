"""Notebook visual launcher using Radeon Cloud rc-tunnel (not cloudflared).

Starts web_http_demo on 127.0.0.1, exposes it with `rc-tunnel`, and embeds the
public https://rc-*.radeon.firstdg.ai URL in an iframe (in-page + external).
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
_PUBLIC_URLS: dict[int, str] = {}


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
        body = "<div style='color:#64748b;text-align:center;padding:24px'>下方嵌入页可上传并对话</div>"
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


def _start_web_for_orch(orch: Any, default_mode: str = "chat", port: int | None = None) -> int:
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

    port = int(port or os.getenv("PLA_NOTEBOOK_UI_PORT", "0") or 0) or _free_port()
    if port not in _EMBED_SERVERS:
        server = web.ThreadingHTTPServer(("127.0.0.1", port), web.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _EMBED_SERVERS[port] = server
    return port


def _rc_tunnel_bin() -> str | None:
    for p in (
        shutil.which("rc-tunnel"),
        str(Path.home() / ".local" / "bin" / "rc-tunnel"),
        "/usr/local/bin/rc-tunnel",
    ):
        if p and Path(p).exists():
            return p
    return None


def _ensure_rc_tunnel() -> str | None:
    existing = _rc_tunnel_bin()
    if existing:
        return existing
    installer = Path("/var/run/secrets/frp-self-service/install")
    if not installer.exists():
        print(
            "[ui] rc-tunnel 未安装。Terminal 执行:\n"
            "  /var/run/secrets/frp-self-service/install\n"
            "  export PATH=\"$HOME/.local/bin:$PATH\"",
            flush=True,
        )
        return None
    try:
        subprocess.run(["bash", str(installer)], check=False, timeout=120)
    except Exception as exc:  # noqa: BLE001
        print(f"[ui] rc-tunnel install failed: {exc}", flush=True)
        return None
    return _rc_tunnel_bin()


def _start_rc_tunnel(port: int) -> str | None:
    if port in _PUBLIC_URLS:
        return _PUBLIC_URLS[port]
    bin_path = _ensure_rc_tunnel()
    if not bin_path:
        return None
    try:
        subprocess.run([bin_path, "stop"], check=False, capture_output=True, text=True, timeout=30)
    except Exception:
        pass
    try:
        proc = subprocess.run(
            [bin_path, "expose", "--port", str(port)],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ui] rc-tunnel expose failed: {exc}", flush=True)
        return None
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    print(out, flush=True)
    m = re.search(r"https://rc-[a-z0-9]+\.radeon\.firstdg\.ai", out)
    if not m:
        m = re.search(r"https://[a-z0-9.-]+\.radeon\.firstdg\.ai", out)
    if not m:
        m = re.search(r"https://[^\s]+", out)
    if not m:
        print("[ui] rc-tunnel did not print a public URL", flush=True)
        return None
    url = m.group(0).rstrip("/")
    _PUBLIC_URLS[port] = url
    print(f"[ui] public={url}", flush=True)
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
        self.public_url: str | None = None
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

        # Prefer fixed 7900 so Terminal rc-tunnel expose --port 7900 matches.
        prefer = int(os.getenv("PLA_NOTEBOOK_UI_PORT", "7900") or 7900)
        port = _start_web_for_orch(self.runner, self.mode, port=prefer)
        self.port = port
        self.local_url = f"http://127.0.0.1:{port}/"
        self.public_url = _start_rc_tunnel(port)
        embed = self.public_url or ""
        clear_output(wait=True)
        if embed:
            display(
                HTML(
                    f"""
<div style="font-family:Segoe UI,PingFang SC,sans-serif;color:#e5e7eb">
  <div style="padding:12px 14px;border-radius:12px;background:#0f172a;border:1px solid #334155;margin-bottom:10px">
    <b style="color:#99f6e4">PrivateLocalAgent</b> · Notebook 内嵌 + 外部页面（rc-tunnel）
    <div style="margin-top:8px;font-size:13px">
      <a href="{escape(embed)}" target="_blank" rel="noopener" style="color:#5eead4">打开外部完整界面</a>
      &nbsp;|&nbsp; 本机 <code style="color:#fbbf24">{escape(self.local_url)}</code>
    </div>
  </div>
  <iframe src="{escape(embed)}" title="PrivateLocalAgent"
    style="width:100%;height:780px;border:1px solid #334155;border-radius:14px;background:#0b1220"></iframe>
</div>
"""
                )
            )
        else:
            display(
                HTML(
                    f"""
<div style="padding:14px;border-radius:12px;background:#0f172a;border:1px solid #334155;color:#e5e7eb;
 font-family:Segoe UI,PingFang SC,sans-serif">
  <b style="color:#fbbf24">本页 iframe 需要 rc-tunnel 公网地址</b>
  <p>本地服务已启动：<code>{escape(self.local_url or "")}</code></p>
  <p>请在 Terminal 执行后，把打印的 https://rc-….radeon.firstdg.ai 发我，或重跑 launch：</p>
  <pre style="background:#111827;padding:10px;border-radius:8px;overflow:auto">
/var/run/secrets/frp-self-service/install
export PATH="$HOME/.local/bin:$PATH"
rc-tunnel stop || true
rc-tunnel expose --port {port}
  </pre>
</div>
"""
                )
            )
        print(f"[ui] local={self.local_url}", flush=True)
        print(f"[ui] public={self.public_url}", flush=True)


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
