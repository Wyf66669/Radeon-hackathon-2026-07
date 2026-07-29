"""Notebook-native visual chat UI (no tunnel / no public port).

Primary judge path on Radeon Cloud: open notebooks/visual_no_tunnel.ipynb
Prompts match Demo video via src.apps.judge_script.JUDGE_SEQUENCE.
"""

from __future__ import annotations

from html import escape
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
.pla-plan {
  margin-top: 6px;
  font-size: 12px;
  color: #fbbf24;
}
.pla-empty {
  color: #64748b;
  text-align: center;
  padding: 48px 12px;
  font-size: 14px;
}
</style>
"""


def _bubbles_html(history: list[dict[str, Any]]) -> str:
    if not history:
        return (
            '<div class="pla-empty">选择模式 → 点推荐问题（与 Demo 视频一致）→ 发送。<br/>'
            "无需隧道 / 无需公网端口。</div>"
        )
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


def render_shell(history: list[dict[str, Any]], subtitle: str = "Notebook 内可视化 · 与 Demo 视频同题") -> str:
    body = _bubbles_html(history)
    return f"""
{CSS}
<div class="pla-shell">
  <div class="pla-brand">PrivateLocalAgent</div>
  <p class="pla-sub">{escape(subtitle)}</p>
  <div class="pla-meta">
    <span class="pla-chip">Track 2</span>
    <span class="pla-chip">Notebook 启动</span>
    <span class="pla-chip">同视频题库</span>
    <span class="pla-chip">无隧道</span>
  </div>
  <div class="pla-chat">{body}</div>
</div>
"""


class NotebookVisualChat:
    """Visual chat panel for Jupyter. Prefer widgets; HTML fallback always works."""

    def __init__(
        self,
        runner: Any,
        plan_fn: Callable[[str], list[str]] | None = None,
        default_mode: str = "chat",
    ) -> None:
        # runner: MultiAgentOrchestrator or any object with .run(q, mode=...)
        self.runner = runner
        self.plan_fn = plan_fn
        self.mode = default_mode
        self.history: list[dict[str, Any]] = []

    def _suggestions(self) -> list[str]:
        primary = prompts_for_mode(self.mode)
        if primary:
            return primary
        return [q for _, q in JUDGE_SEQUENCE[:5]]

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
        tips = w.ToggleButtons(options=self._suggestions(), description="")
        box_q = w.Textarea(
            value=(self._suggestions()[0] if self._suggestions() else ""),
            placeholder="输入问题…（推荐问题与 Demo 视频一致）",
            layout=w.Layout(width="100%", height="72px"),
        )
        btn = w.Button(description="发送", button_style="success")
        clear_btn = w.Button(description="清空对话")
        status = w.HTML(
            value="<span style='color:#94a3b8'>就绪 · Notebook 内运行 · 无需隧道</span>"
        )

        def refresh_tips(_: Any = None) -> None:
            self.mode = str(mode_dd.value)
            opts = self._suggestions()
            tips.options = opts
            if opts:
                tips.value = opts[0]
                box_q.value = opts[0]

        def on_tip(change: dict[str, Any]) -> None:
            if change.get("name") == "value" and change.get("new"):
                box_q.value = str(change["new"])

        def redraw() -> None:
            shell.value = render_shell(self.history)

        def on_send(_: Any) -> None:
            q = box_q.value.strip()
            if not q:
                status.value = "<span style='color:#f59e0b'>请输入问题</span>"
                return
            self.mode = str(mode_dd.value)
            status.value = "<span style='color:#99f6e4'>思考中（本地推理约 30–90 秒）…</span>"
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
        btn.on_click(on_send)
        clear_btn.on_click(on_clear)

        ui = w.VBox(
            [
                shell,
                mode_dd,
                w.HTML(
                    "<div style='color:#94a3b8;font-size:12px;margin:8px 0 4px'>"
                    "推荐问题（= Demo 视频 / START_HERE.md）</div>"
                ),
                tips,
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
) -> NotebookVisualChat:
    """runner = MultiAgentOrchestrator (preferred) or compatible .run(q, mode=...)."""
    ui = NotebookVisualChat(runner, plan_fn=plan_fn, default_mode=default_mode)
    ui.show()
    return ui
