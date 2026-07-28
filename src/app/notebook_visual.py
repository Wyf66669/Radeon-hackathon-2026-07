"""Notebook-native visual chat UI (no tunnel / no public port).

Runs inside JupyterLab via IPython display + optional ipywidgets.
The browser talks to the notebook kernel WebSocket only — no rc-tunnel, no /proxy.
"""

from __future__ import annotations

from html import escape
from typing import Any, Callable

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
        return '<div class="pla-empty">输入问题后点击发送。推荐问题可一键填入。</div>'
    parts: list[str] = []
    for turn in history:
        q = escape(str(turn.get("q", "")))
        a = escape(str(turn.get("a", "")))
        tools = escape(", ".join(turn.get("tools") or []) or "—")
        plan = escape(" → ".join(turn.get("plan") or []) or "—")
        parts.append(f'<div class="pla-row user"><div class="pla-bubble user">{q}</div></div>')
        parts.append(
            "<div class='pla-row bot'><div class='pla-bubble bot'>"
            f"{a}"
            f"<div class='pla-tools'>Tools: {tools}</div>"
            f"<div class='pla-plan'>Plan: {plan}</div>"
            "</div></div>"
        )
    return "\n".join(parts)


def render_shell(history: list[dict[str, Any]], subtitle: str = "Notebook 内可视化 · 无需隧道/代理") -> str:
    body = _bubbles_html(history)
    return f"""
{CSS}
<div class="pla-shell">
  <div class="pla-brand">PrivateLocalAgent</div>
  <p class="pla-sub">{escape(subtitle)}</p>
  <div class="pla-meta">
    <span class="pla-chip">Track 2</span>
    <span class="pla-chip">本地 RAG</span>
    <span class="pla-chip">工具调用</span>
    <span class="pla-chip">无隧道</span>
  </div>
  <div class="pla-chat">{body}</div>
</div>
"""


class NotebookVisualChat:
    """Visual chat panel for Jupyter. Prefer widgets; HTML fallback always works."""

    SUGGESTIONS = [
        "VPN 密码怎么重置？",
        "涉密文档可以用哪些 AI 工具？",
        "请假需要提前几天申请？",
        "GPU 推理环境有什么要求？",
        "知识库里有哪些 IT FAQ？",
    ]

    def __init__(
        self,
        agent: Any,
        plan_fn: Callable[[str], list[str]] | None = None,
    ) -> None:
        self.agent = agent
        self.plan_fn = plan_fn
        self.history: list[dict[str, Any]] = []
        self._out = None

    def _run(self, query: str) -> dict[str, Any]:
        query = (query or "").strip()
        if not query:
            raise ValueError("问题不能为空")
        plan = self.plan_fn(query) if self.plan_fn else []
        result = self.agent.run(query)
        turn = {
            "q": query,
            "a": result.answer,
            "tools": list(result.used_tools or []),
            "plan": list(plan or []),
        }
        self.history.append(turn)
        return turn

    def ask(self, query: str) -> None:
        """Non-widget API: run question and redraw HTML panel."""
        from IPython.display import HTML, clear_output, display

        clear_output(wait=True)
        display(HTML(render_shell(self.history, subtitle="处理中…")))
        self._run(query)
        clear_output(wait=True)
        display(HTML(render_shell(self.history)))

    def show(self) -> None:
        """Launch interactive UI inside the notebook (no tunnel)."""
        from IPython.display import HTML, clear_output, display

        try:
            import ipywidgets as w
        except Exception as exc:  # noqa: BLE001
            display(HTML(render_shell(self.history)))
            print("ipywidgets 不可用，改用 ui.ask('你的问题')。原因:", exc)
            return

        shell = w.HTML(value=render_shell(self.history))
        box_q = w.Textarea(
            value=self.SUGGESTIONS[0],
            placeholder="输入问题…",
            layout=w.Layout(width="100%", height="72px"),
        )
        tips = w.ToggleButtons(
            options=self.SUGGESTIONS,
            description="",
            style={"button_width": "auto"},
        )
        btn = w.Button(description="发送", button_style="success")
        clear_btn = w.Button(description="清空对话")
        status = w.HTML(value="<span style='color:#94a3b8'>就绪 · 无需隧道</span>")

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
            status.value = "<span style='color:#99f6e4'>思考中（约 30–90 秒）…</span>"
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

        tips.observe(on_tip, names="value")
        btn.on_click(on_send)
        clear_btn.on_click(on_clear)

        ui = w.VBox(
            [
                shell,
                w.HTML("<div style='color:#94a3b8;font-size:12px;margin:8px 0 4px'>推荐问题</div>"),
                tips,
                box_q,
                w.HBox([btn, clear_btn]),
                status,
            ],
            layout=w.Layout(width="100%"),
        )
        clear_output(wait=True)
        display(ui)


def launch_notebook_visual(agent: Any, plan_fn: Callable[[str], list[str]] | None = None) -> NotebookVisualChat:
    ui = NotebookVisualChat(agent, plan_fn=plan_fn)
    ui.show()
    return ui
