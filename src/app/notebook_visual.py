"""Notebook-native visual chat UI (no tunnel / no public port).

Primary judge path on Radeon Cloud: open notebooks/visual_no_tunnel.ipynb
Prompts match Demo video via src.apps.judge_script.JUDGE_SEQUENCE.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Any, Callable

from src.apps.judge_script import JUDGE_SEQUENCE, prompts_for_mode
from src.apps.modes import UI_MODES

CSS = """
<style>
.pla-shell {
  font-family: "IBM Plex Sans", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 920px;
  margin: 0 auto;
  padding: 18px 16px 28px;
  border-radius: 18px;
  color: #e5e7eb;
  background:
    radial-gradient(900px 380px at 8% -20%, rgba(20,184,166,.22), transparent 55%),
    radial-gradient(700px 320px at 100% 0%, rgba(245,158,11,.10), transparent 50%),
    #0f172a;
  border: 1px solid #334155;
}
.pla-brand {
  font-size: 28px;
  font-weight: 750;
  letter-spacing: -0.03em;
  margin: 0 0 4px;
  color: #f8fafc;
}
.pla-sub {
  margin: 0 0 16px;
  color: #94a3b8;
  font-size: 14px;
}
.pla-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.pla-chip {
  font-size: 12px;
  color: #99f6e4;
  background: rgba(20,184,166,.12);
  border: 1px solid rgba(20,184,166,.35);
  border-radius: 999px;
  padding: 4px 10px;
}
.pla-chat {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 220px;
  max-height: 520px;
  overflow-y: auto;
  padding: 12px;
  border-radius: 14px;
  background: rgba(15,23,42,.65);
  border: 1px solid #1f2937;
}
.pla-row { display: flex; }
.pla-row.user { justify-content: flex-end; }
.pla-row.bot { justify-content: flex-start; }
.pla-bubble {
  max-width: 86%;
  padding: 12px 14px;
  border-radius: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}
.pla-bubble.user {
  background: linear-gradient(180deg, #14b8a6, #0d9488);
  color: #042f2e;
  font-weight: 600;
  border-bottom-right-radius: 4px;
}
.pla-bubble.bot {
  background: #1f2937;
  color: #e5e7eb;
  border: 1px solid #334155;
  border-bottom-left-radius: 4px;
}
.pla-tools {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}
.pla-empty {
  color: #64748b;
  text-align: center;
  padding: 48px 12px;
  font-size: 14px;
}
</style>
"""

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _bubbles_html(history: list[dict[str, Any]]) -> str:
    if not history:
        return '<div class="pla-empty">选择模式 → 可上传图片 → 点推荐问题 → 发送</div>'
    parts: list[str] = []
    for turn in history:
        q = escape(str(turn.get("q", "")))
        a = escape(str(turn.get("a", "")))
        tools = escape(", ".join(turn.get("tools") or []) or "—")
        mode = escape(str(turn.get("mode") or "—"))
        parts.append(f'<div class="pla-row user"><div class="pla-bubble user">{q}</div></div>')
        parts.append(
            "<div class='pla-row bot'><div class='pla-bubble bot'>"
            f"{a}"
            f"<div class='pla-tools'>Mode: {mode} · Tools: {tools}</div>"
            "</div></div>"
        )
    return "\n".join(parts)


def render_shell(history: list[dict[str, Any]], subtitle: str = "本地私有 Agent") -> str:
    body = _bubbles_html(history)
    return f"""
{CSS}
<div class="pla-shell">
  <div class="pla-brand">PrivateLocalAgent</div>
  <p class="pla-sub">{escape(subtitle)}</p>
  <div class="pla-meta">
    <span class="pla-chip">Track 2</span>
    <span class="pla-chip">Notebook</span>
    <span class="pla-chip">Local / Private</span>
  </div>
  <div class="pla-chat">{body}</div>
</div>
"""


def _safe_image_name(name: str) -> str:
    base = Path(name or "upload.png").name
    base = re.sub(r"[^\w.\-]+", "_", base, flags=re.UNICODE)
    if Path(base).suffix.lower() not in _IMAGE_EXTS:
        base = f"{Path(base).stem or 'upload'}.png"
    return base[:120]


def _fileupload_payload(value: Any) -> list[tuple[str, bytes]]:
    """Normalize ipywidgets FileUpload value across v7/v8."""
    out: list[tuple[str, bytes]] = []
    if not value:
        return out
    # v7: dict[name -> {metadata, content}]
    if isinstance(value, dict):
        for name, meta in value.items():
            content = meta.get("content") if isinstance(meta, dict) else None
            if content is None:
                continue
            out.append((str(name), bytes(content)))
        return out
    # v8: tuple of UploadedFile / dict-like
    for item in value:
        if isinstance(item, dict):
            name = str(item.get("name") or "upload.png")
            content = item.get("content") or b""
            out.append((name, bytes(content)))
        else:
            name = str(getattr(item, "name", "upload.png"))
            content = getattr(item, "content", b"")
            out.append((name, bytes(content)))
    return out


class NotebookVisualChat:
    """Visual chat panel for Jupyter. Prefer widgets; HTML fallback always works."""

    def __init__(
        self,
        runner: Any,
        plan_fn: Callable[[str], list[str]] | None = None,
        default_mode: str = "chat",
        upload_dir: Path | str | None = None,
    ) -> None:
        # runner: MultiAgentOrchestrator or any object with .run(q, mode=...)
        self.runner = runner
        self.plan_fn = plan_fn
        self.mode = default_mode
        self.history: list[dict[str, Any]] = []
        self.last_image: str | None = None
        self.upload_dir = self._resolve_upload_dir(upload_dir)

    def _resolve_upload_dir(self, upload_dir: Path | str | None) -> Path:
        if upload_dir:
            path = Path(upload_dir)
        else:
            tools = getattr(self.runner, "tools", None)
            ud = getattr(tools, "upload_dir", None)
            if ud:
                path = Path(ud)
            else:
                from src.config import load_settings

                path = load_settings().resolve("data/uploads")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_upload(self, filename: str, content: bytes) -> Path:
        if not content:
            raise ValueError("空文件")
        if len(content) > 12 * 1024 * 1024:
            raise ValueError("图片过大（上限 12MB）")
        name = _safe_image_name(filename)
        target = self.upload_dir / name
        target.write_bytes(content)
        self.last_image = name
        return target

    def _suggestions(self) -> list[str]:
        primary = prompts_for_mode(self.mode)
        if primary:
            return primary
        return [q for _, q in JUDGE_SEQUENCE[:5]]

    def _run(self, query: str) -> dict[str, Any]:
        query = (query or "").strip()
        if not query:
            raise ValueError("问题不能为空")
        # Prefer the file just uploaded via the chat uploader.
        if self.mode == "vision" and self.last_image and "解析" in query and Path(query).suffix == "":
            # Keep natural prompt; parse_image picks newest mtime under upload_dir.
            pass
        result = self.runner.run(query, mode=self.mode)
        turn = {
            "q": query,
            "a": getattr(result, "answer", str(result)),
            "tools": list(getattr(result, "used_tools", None) or []),
            "mode": getattr(result, "app_mode", None) or self.mode,
        }
        self.history.append(turn)
        return turn

    def ask(self, query: str, mode: str | None = None) -> None:
        from IPython.display import HTML, clear_output, display

        if mode:
            self.mode = mode
        clear_output(wait=True)
        display(HTML(render_shell(self.history, subtitle="处理中…")))
        self._run(query)
        clear_output(wait=True)
        display(HTML(render_shell(self.history)))

    def show(self) -> None:
        from IPython.display import HTML, clear_output, display

        try:
            import ipywidgets as w
        except Exception as exc:  # noqa: BLE001
            display(HTML(render_shell(self.history)))
            print("ipywidgets 不可用，改用 ui.ask('问题', mode='rag')。原因:", exc)
            return

        mode_labels = [(m.title, m.id) for m in UI_MODES]
        mode_dd = w.Dropdown(
            options=mode_labels,
            value=self.mode if self.mode in {m.id for m in UI_MODES} else "chat",
            description="模式",
            layout=w.Layout(width="360px"),
        )
        shell = w.HTML(value=render_shell(self.history))
        tips = w.Dropdown(
            options=self._suggestions() or [""],
            description="推荐",
            layout=w.Layout(width="100%"),
        )
        box_q = w.Textarea(
            value=(self._suggestions()[0] if self._suggestions() else ""),
            placeholder="输入问题…",
            layout=w.Layout(width="100%", height="72px"),
        )
        upload_label = w.HTML(
            value=(
                "<div style='margin:10px 0 6px;padding:10px 12px;border:1px dashed #14b8a6;"
                "border-radius:10px;background:rgba(20,184,166,.08);color:#99f6e4'>"
                "<b>上传图片</b>：点下方按钮选择 png/jpg，成功后会自动切到「图文解析」"
                "</div>"
            )
        )
        try:
            uploader = w.FileUpload(
                accept=".png,.jpg,.jpeg,.webp,.bmp,image/*",
                multiple=False,
                description="选择图片文件",
                button_style="info",
                layout=w.Layout(width="280px", height="40px"),
            )
        except TypeError:
            # older ipywidgets without button_style
            uploader = w.FileUpload(
                accept=".png,.jpg,.jpeg,.webp,.bmp,image/*",
                multiple=False,
                description="选择图片文件",
                layout=w.Layout(width="280px"),
            )
        upload_hint = w.HTML(
            value="<span style='color:#94a3b8;font-size:12px'>还没选文件</span>"
        )
        path_box = w.Text(
            value="",
            placeholder="或粘贴已有图片路径 / 文件名（uploads 目录内）",
            layout=w.Layout(width="70%"),
        )
        path_btn = w.Button(description="使用该图片", button_style="warning")
        btn = w.Button(description="发送", button_style="success")
        clear_btn = w.Button(description="清空对话")
        status = w.HTML(value="<span style='color:#94a3b8'>就绪</span>")

        def refresh_tips(_: Any = None) -> None:
            self.mode = str(mode_dd.value)
            opts = self._suggestions() or [""]
            tips.unobserve(on_tip, names="value")
            tips.options = opts
            tips.value = opts[0]
            tips.observe(on_tip, names="value")
            box_q.value = opts[0]

        def on_tip(change: dict[str, Any]) -> None:
            if change.get("name") == "value" and change.get("new"):
                box_q.value = str(change["new"])

        def redraw() -> None:
            shell.value = render_shell(self.history)

        def _after_image_ready(saved_name: str) -> None:
            mode_dd.value = "vision"
            self.mode = "vision"
            refresh_tips()
            box_q.value = "解析刚上传的图片"
            status.value = (
                f"<span style='color:#6ee7b7'>已就绪: {escape(saved_name)} · 点发送</span>"
            )
            upload_hint.value = (
                f"<span style='color:#99f6e4;font-size:12px'>当前图片: {escape(saved_name)}</span>"
            )

        def on_upload(change: dict[str, Any]) -> None:
            if change.get("name") != "value":
                return
            files = _fileupload_payload(change.get("new"))
            if not files:
                return
            name, content = files[-1]
            try:
                saved = self.save_upload(name, content)
            except Exception as exc:  # noqa: BLE001
                status.value = f"<span style='color:#f87171'>上传失败: {escape(str(exc))}</span>"
                return
            _after_image_ready(saved.name)

        def on_path(_: Any) -> None:
            raw = (path_box.value or "").strip().strip('"').strip("'")
            if not raw:
                status.value = "<span style='color:#f59e0b'>请填写图片路径或文件名</span>"
                return
            src = Path(raw)
            if not src.is_file():
                cand = self.upload_dir / Path(raw).name
                if cand.is_file():
                    src = cand
                else:
                    status.value = f"<span style='color:#f87171'>找不到文件: {escape(raw)}</span>"
                    return
            try:
                saved = self.save_upload(src.name, src.read_bytes())
            except Exception as exc:  # noqa: BLE001
                status.value = f"<span style='color:#f87171'>读取失败: {escape(str(exc))}</span>"
                return
            _after_image_ready(saved.name)

        def on_send(_: Any) -> None:
            q = box_q.value.strip()
            if not q:
                status.value = "<span style='color:#f59e0b'>请输入问题</span>"
                return
            self.mode = str(mode_dd.value)
            status.value = "<span style='color:#99f6e4'>思考中…</span>"
            btn.disabled = True
            try:
                self._run(q)
                redraw()
                status.value = "<span style='color:#6ee7b7'>完成</span>"
            except Exception as exc:  # noqa: BLE001
                status.value = f"<span style='color:#f87171'>错误: {escape(str(exc))}</span>"
            finally:
                btn.disabled = False

        def on_clear(_: Any) -> None:
            self.history.clear()
            redraw()
            status.value = "<span style='color:#94a3b8'>已清空</span>"

        mode_dd.observe(refresh_tips, names="value")
        tips.observe(on_tip, names="value")
        uploader.observe(on_upload, names="value")
        path_btn.on_click(on_path)
        btn.on_click(on_send)
        clear_btn.on_click(on_clear)

        ui = w.VBox(
            [
                shell,
                mode_dd,
                tips,
                upload_label,
                w.HBox([uploader, upload_hint]),
                w.HBox([path_box, path_btn]),
                box_q,
                w.HBox([btn, clear_btn]),
                status,
            ],
            layout=w.Layout(width="100%"),
        )
        clear_output(wait=True)
        display(ui)


def launch_notebook_visual(
    runner: Any,
    plan_fn: Callable[[str], list[str]] | None = None,
    default_mode: str = "chat",
    upload_dir: Path | str | None = None,
) -> NotebookVisualChat:
    """runner = MultiAgentOrchestrator (preferred) or compatible .run(q, mode=...)."""
    ui = NotebookVisualChat(
        runner,
        plan_fn=plan_fn,
        default_mode=default_mode,
        upload_dir=upload_dir,
    )
    ui.show()
    return ui
