#!/usr/bin/env python3
"""Generate an improved 3–5 min Track 2 demo MP4 for PrivateLocalAgent.

Higher-quality slides + UI mocks + typed terminal, encoded with H.264.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "demo_assets"
OUT_MP4 = OUT_DIR / "PrivateLocalAgent_demo.mp4"
W, H = 1280, 720
FPS = 8  # smoother; total duration set by scene seconds


# Brand palette (teal / slate — avoid purple defaults)
C_BG = (8, 18, 32)
C_PANEL = (15, 23, 42)
C_CARD = (30, 41, 59)
C_LINE = (51, 65, 85)
C_TEXT = (241, 245, 249)
C_MUTED = (148, 163, 184)
C_ACCENT = (20, 184, 166)
C_ACCENT2 = (13, 148, 136)
C_OK = (52, 211, 153)
C_WARN = (251, 191, 36)
C_USER = (15, 118, 110)
C_LIGHT = (248, 250, 252)


def _ensure_deps():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    return Image, ImageDraw, ImageFont, ImageFilter


def font(size: int, ImageFont, bold: bool = False):
    names = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        p = Path(name)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_lines(text: str, width: int = 70) -> list[str]:
    out: list[str] = []
    for para in text.splitlines():
        if not para.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(para, width=width) or [""])
    return out


def gradient_bg(Image, ImageDraw, top=(6, 28, 48), bottom=(8, 12, 24)):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(1, H - 1)
        c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        d.line((0, y, W, y), fill=c)
    # soft vignette arcs
    d.ellipse((-200, -180, 420, 360), outline=(20, 80, 90), width=2)
    d.ellipse((900, 400, 1500, 980), outline=(20, 70, 80), width=2)
    return img


def progress_bar(d, ImageFont, t: float, label: str):
    """t in [0,1] overall timeline."""
    d.rectangle((0, H - 28, W, H), fill=(2, 6, 16))
    d.rectangle((0, H - 28, int(W * max(0, min(1, t))), H), fill=C_ACCENT)
    d.text((16, H - 24), label[:80], fill=C_MUTED, font=font(14, ImageFont))


def hold(img, seconds: float) -> list:
    n = max(1, int(seconds * FPS))
    return [img.copy() for _ in range(n)]


def fade(a, b, seconds: float = 0.4) -> list:
    n = max(2, int(seconds * FPS))
    frames = []
    for i in range(n):
        alpha = (i + 1) / n
        frames.append(Image.blend(a, b, alpha))
    return frames


def scene_title(Image, ImageDraw, ImageFont, ImageFilter) -> list:
    frames = []
    base = gradient_bg(Image, ImageDraw)
    for i in range(int(2.5 * FPS)):
        img = base.copy()
        d = ImageDraw.Draw(img)
        # rising brand block
        rise = int(40 * (1 - math.exp(-i / 8)))
        d.rounded_rectangle((60, 180 + 40 - rise, 1220, 520 + 40 - rise), radius=28, fill=C_PANEL)
        d.rectangle((60, 180 + 40 - rise, 72, 520 + 40 - rise), fill=C_ACCENT)
        alpha_y = 210 + 40 - rise
        d.text((100, alpha_y), "PrivateLocalAgent", fill=C_ACCENT, font=font(58, ImageFont, bold=True))
        d.text((100, alpha_y + 80), "Track 2 · 说干就干 · Wyf66669", fill=C_TEXT, font=font(30, ImageFont))
        d.text((100, alpha_y + 130), "本地私有 RAG Agent · AMD Radeon GPU + ROCm", fill=C_MUTED, font=font(24, ImageFont))
        d.text((100, alpha_y + 190), "Demo · ROCm · RAG · Tools · Privacy · Multi-agent", fill=C_OK, font=font(20, ImageFont))
        progress_bar(d, ImageFont, 0.02, "00:00  Opening")
        frames.append(img)
    # hold
    frames += hold(frames[-1], 8.0)
    return frames


def scene_cloud_ready(Image, ImageDraw, ImageFont) -> list:
    img = gradient_bg(Image, ImageDraw)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((80, 80, 1200, 620), radius=20, fill=C_PANEL)
    d.text((110, 110), "Radeon Cloud · Active Instance", fill=C_TEXT, font=font(32, ImageFont, bold=True))
    d.text((110, 160), "Template: AMD OneClick Base (ROCm)   Status: Ready", fill=C_MUTED, font=font(20, ImageFont))
    # cards
    cards = [
        ("GPU", "AMD Radeon", C_OK),
        ("Stack", "ROCm + HIP", C_ACCENT),
        ("Mode", "local_transformers", C_WARN),
        ("Team", "说干就干", C_TEXT),
    ]
    x = 110
    for title, val, color in cards:
        d.rounded_rectangle((x, 230, x + 240, 380), radius=16, fill=C_CARD, outline=C_LINE, width=2)
        d.text((x + 24, 260), title, fill=C_MUTED, font=font(18, ImageFont))
        d.text((x + 24, 300), val, fill=color, font=font(24, ImageFont, bold=True))
        x += 270
    d.text((110, 440), "赛道二：私有 AI 智能体本地部署", fill=C_TEXT, font=font(26, ImageFont))
    d.text((110, 490), "全离线优先 · 知识库不出域 · Tool Calling · 任务规划", fill=C_MUTED, font=font(22, ImageFont))
    progress_bar(d, ImageFont, 0.10, "00:20  Cloud instance ready")
    return hold(img, 14)


def scene_terminal_typed(
    Image,
    ImageDraw,
    ImageFont,
    title: str,
    lines: list[str],
    seconds: float,
    progress: float,
    clock: str,
) -> list:
    frames = []
    total_chars = sum(len(x) + 1 for x in lines)
    steps = max(1, int(seconds * FPS))
    f_mono = font(20, ImageFont)
    for step in range(steps):
        target = int((step + 1) / steps * total_chars)
        img = gradient_bg(Image, ImageDraw, top=(10, 16, 28), bottom=(4, 8, 16))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((48, 56, W - 48, H - 56), radius=18, fill=(2, 6, 16), outline=C_ACCENT, width=2)
        # traffic lights
        for i, c in enumerate([(248, 113, 113), (251, 191, 36), (74, 222, 128)]):
            d.ellipse((70 + i * 28, 74, 86 + i * 28, 90), fill=c)
        d.text((180, 70), title, fill=C_MUTED, font=font(18, ImageFont))
        y = 120
        count = 0
        done = False
        for raw in lines:
            chunk = ""
            for ch in raw + "\n":
                count += 1
                if count > target:
                    done = True
                    break
                chunk += ch
            for line in wrap_lines(chunk.rstrip("\n"), 86):
                color = C_MUTED
                if line.startswith("$") or line.startswith("==="):
                    color = C_ACCENT
                if any(k in line for k in ("cuda_available: True", "3 个工作日", "kb_search", "matmul_ok", "ready")):
                    color = C_OK
                if line.startswith("Q:") or line.startswith("A:"):
                    color = C_TEXT
                d.text((70, y), line, fill=color, font=f_mono)
                y += 26
                if y > H - 80:
                    break
            if done or y > H - 80:
                break
        # caret
        if not done and step % 4 < 2:
            d.rectangle((70, y, 78, y + 18), fill=C_ACCENT)
        progress_bar(d, ImageFont, progress, f"{clock}  {title}")
        frames.append(img)
    # brief hold on final
    frames += hold(frames[-1], 2.0)
    return frames


def scene_notebook(Image, ImageDraw, ImageFont) -> list:
    img = Image.new("RGB", (W, H), (226, 232, 240))
    d = ImageDraw.Draw(img)
    # jupyter chrome
    d.rectangle((0, 0, W, 48), fill=(55, 65, 81))
    d.text((16, 12), "JupyterLab  ·  notebooks/private_agent_demo.ipynb", fill=C_TEXT, font=font(18, ImageFont))
    d.rectangle((0, 48, 220, H), fill=(241, 245, 249))
    d.text((20, 70), "File Browser", fill=(71, 85, 105), font=font(16, ImageFont, bold=True))
    for i, name in enumerate(["src/", "scripts/", "notebooks/", "docs/", "data/"]):
        d.text((28, 110 + i * 32), name, fill=(51, 65, 85), font=font(16, ImageFont))
    d.rounded_rectangle((240, 70, 1240, 200), radius=10, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    d.text((260, 90), "In [1]:  # one-cell visual demo — no tunnel", fill=(15, 23, 42), font=font(18, ImageFont))
    d.text((260, 130), "rt = bootstrap(); panel  # wait until ready", fill=(71, 85, 105), font=font(18, ImageFont))
    d.rounded_rectangle((240, 230, 1240, 640), radius=12, fill=(15, 23, 42))
    d.text((270, 270), "PrivateLocalAgent", fill=C_ACCENT, font=font(28, ImageFont, bold=True))
    d.text((270, 320), "Status: ready   ·   Backend: local_transformers (ROCm)", fill=C_OK, font=font(20, ImageFont))
    d.text((270, 370), "KB chunks loaded  ·  Tools online  ·  Memory ready", fill=C_MUTED, font=font(20, ImageFont))
    d.rounded_rectangle((270, 440, 1180, 560), radius=14, fill=C_CARD)
    d.text((300, 470), "输入问题…  例：请假需要提前几天申请？", fill=C_MUTED, font=font(22, ImageFont))
    d.rounded_rectangle((980, 480, 1150, 530), radius=10, fill=C_ACCENT2)
    d.text((1020, 492), "发送", fill=C_TEXT, font=font(20, ImageFont, bold=True))
    progress_bar(d, ImageFont, 0.28, "01:20  Notebook visual UI (tunnel-free)")
    return hold(img, 16)


def scene_chat(
    Image,
    ImageDraw,
    ImageFont,
    q: str,
    tools: str,
    answer: str,
    seconds: float,
    progress: float,
    clock: str,
    light: bool = True,
) -> list:
    frames = []
    steps = max(1, int(seconds * FPS))
    # reveal answer gradually
    for step in range(steps):
        frac = (step + 1) / steps
        img = Image.new("RGB", (W, H), C_LIGHT if light else C_BG)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, W, 64), fill=C_USER)
        d.text((28, 16), "PrivateLocalAgent · Chat", fill=(255, 255, 255), font=font(26, ImageFont, bold=True))
        # user bubble right
        d.rounded_rectangle((520, 100, 1230, 200), radius=18, fill=C_USER)
        for i, line in enumerate(wrap_lines(q, 38)[:3]):
            d.text((545, 120 + i * 28), line, fill=(255, 255, 255), font=font(22, ImageFont))
        # assistant
        d.rounded_rectangle((50, 240, 980, 620), radius=18, fill=(255, 255, 255) if light else C_PANEL, outline=C_LINE, width=2)
        d.text((75, 260), f"Tools: {tools}", fill=C_ACCENT2, font=font(18, ImageFont, bold=True))
        shown = answer[: max(1, int(len(answer) * frac))]
        y = 300
        for line in wrap_lines(shown, 46):
            d.text((75, y), line, fill=(30, 41, 59) if light else C_TEXT, font=font(22, ImageFont))
            y += 30
            if y > 580:
                break
        progress_bar(d, ImageFont, progress, f"{clock}  Chat demo")
        frames.append(img)
    frames += hold(frames[-1], 2.5)
    return frames


def scene_architecture(Image, ImageDraw, ImageFont) -> list:
    img = gradient_bg(Image, ImageDraw)
    d = ImageDraw.Draw(img)
    d.text((70, 50), "Architecture · local-first", fill=C_TEXT, font=font(34, ImageFont, bold=True))
    boxes = [
        (70, 130, 300, 250, "UI / Notebook", "HTTP · Gradio · CLI"),
        (360, 130, 620, 250, "Orchestrator", "plan · route · reflect"),
        (680, 130, 980, 250, "LLM (ROCm)", "local_transformers"),
        (70, 300, 300, 420, "RAG / Chroma", "private KB"),
        (360, 300, 620, 420, "Tools", "kb_search · files · OCR"),
        (680, 300, 980, 420, "Memory", "session facts"),
        (1020, 130, 1210, 420, "Privacy", "guard + audit"),
    ]
    for x1, y1, x2, y2, t, s in boxes:
        d.rounded_rectangle((x1, y1, x2, y2), radius=14, fill=C_PANEL, outline=C_ACCENT, width=2)
        d.text((x1 + 18, y1 + 28), t, fill=C_ACCENT, font=font(20, ImageFont, bold=True))
        d.text((x1 + 18, y1 + 70), s, fill=C_MUTED, font=font(16, ImageFont))
    # arrows as lines
    for x in (300, 620, 980):
        d.line((x, 190, x + 50, 190), fill=C_MUTED, width=3)
    d.text((70, 470), "Workflow: requirement → YAML → export (Dify / LangChain / JSON)", fill=C_TEXT, font=font(22, ImageFont))
    d.text((70, 520), "Six apps + 图文解析(OCR) + skills scaffolding (real files)", fill=C_MUTED, font=font(20, ImageFont))
    progress_bar(d, ImageFont, 0.82, "04:10  Architecture")
    return hold(img, 18)


def scene_features(Image, ImageDraw, ImageFont) -> list:
    img = gradient_bg(Image, ImageDraw)
    d = ImageDraw.Draw(img)
    d.text((70, 60), "Highlights for judges", fill=C_TEXT, font=font(34, ImageFont, bold=True))
    items = [
        ("01", "Grounded RAG", "强制 kb_search，中文政策问答可核验"),
        ("02", "AMD ROCm", "verify_rocm + bench_rocm 可复现"),
        ("03", "Privacy-first", "涉密场景仅本地 / 批准模型"),
        ("04", "Multi-agent", "编排器 + 六大办公场景应用"),
        ("05", "Workflow export", "需求 → YAML → 多格式导出"),
        ("06", "Vision OCR", "图文解析，数据不出设备"),
    ]
    for i, (n, t, s) in enumerate(items):
        col = i % 3
        row = i // 3
        x = 70 + col * 390
        y = 140 + row * 220
        d.rounded_rectangle((x, y, x + 360, y + 180), radius=16, fill=C_PANEL, outline=C_LINE, width=2)
        d.text((x + 24, y + 28), n, fill=C_ACCENT, font=font(22, ImageFont, bold=True))
        d.text((x + 24, y + 70), t, fill=C_TEXT, font=font(24, ImageFont, bold=True))
        for j, line in enumerate(wrap_lines(s, 18)[:2]):
            d.text((x + 24, y + 110 + j * 28), line, fill=C_MUTED, font=font(18, ImageFont))
    progress_bar(d, ImageFont, 0.72, "03:40  Feature grid")
    return hold(img, 18)


def scene_closing(Image, ImageDraw, ImageFont) -> list:
    img = gradient_bg(Image, ImageDraw, top=(6, 40, 50), bottom=(4, 12, 24))
    d = ImageDraw.Draw(img)
    d.text((80, 160), "Thank you", fill=C_ACCENT, font=font(56, ImageFont, bold=True))
    lines = [
        "PR title: Track 2, 说干就干, PrivateLocalAgent",
        "Repo: Wyf66669/Radeon-hackathon-2026-07",
        "Branch: track2-private-local-agent",
        "PR: AMD-DEV-CONTEST/.../pull/40",
    ]
    y = 260
    for line in lines:
        d.text((80, y), line, fill=C_TEXT, font=font(26, ImageFont))
        y += 48
    d.text((80, 520), "本地私有 · 可复现 · 面向办公落地", fill=C_OK, font=font(24, ImageFont))
    progress_bar(d, ImageFont, 1.0, "04:50  Closing")
    return hold(img, 16)


def find_ffmpeg() -> str | None:
    which = shutil.which("ffmpeg")
    if which:
        return which
    for cand in (r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"):
        if Path(cand).exists():
            return cand
    return None


def encode(frames: list, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_DIR / "_frames_v2"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, fr in enumerate(frames):
        p = tmp / f"f_{i:05d}.png"
        fr.save(p, optimize=True)
        paths.append(p)

    ffmpeg = find_ffmpeg()
    if ffmpeg:
        # high quality H.264; CFR from image sequence
        pattern = str(tmp / "f_%05d.png")
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            pattern,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            "-preset",
            "medium",
            "-movflags",
            "+faststart",
            str(out),
        ]
        subprocess.check_call(cmd)
    else:
        try:
            import imageio.v2 as imageio
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "imageio", "imageio-ffmpeg"])
            import imageio.v2 as imageio

        writer = imageio.get_writer(str(out), fps=FPS, codec="libx264", quality=7)
        for p in paths:
            writer.append_data(imageio.imread(p))
        writer.close()

    # cleanup frames to save disk
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    Image, ImageDraw, ImageFont, ImageFilter = _ensure_deps()
    frames: list = []

    frames += scene_title(Image, ImageDraw, ImageFont, ImageFilter)
    frames += scene_cloud_ready(Image, ImageDraw, ImageFont)
    frames += scene_terminal_typed(
        Image,
        ImageDraw,
        ImageFont,
        "Terminal · verify_rocm.py",
        [
            "$ python scripts/verify_rocm.py",
            "=== PrivateLocalAgent · GPU / ROCm check ===",
            "torch: 2.x+rocm",
            "cuda_available: True",
            "hip: enabled",
            "device_count: 1",
            "device0: AMD Radeon Graphics",
            "matmul_ok: torch.Size([1024, 1024])",
        ],
        seconds=24,
        progress=0.18,
        clock="00:40",
    )
    frames += scene_notebook(Image, ImageDraw, ImageFont)
    frames += scene_terminal_typed(
        Image,
        ImageDraw,
        ImageFont,
        "Terminal · demo_cli.py",
        [
            "$ python scripts/demo_cli.py",
            "Q: 请假需要提前几天申请？",
            "Plan:",
            "  1. Search private knowledge base",
            "  2. Ground answer in retrieved policy",
            "Route: specialist",
            "Tools: kb_search",
            "A: 根据公司请假制度，请假需提前 3 个工作日申请。",
        ],
        seconds=26,
        progress=0.42,
        clock="02:00",
    )
    frames += scene_chat(
        Image,
        ImageDraw,
        ImageFont,
        "请假需要提前几天申请？",
        "kb_search",
        "根据公司请假制度，请假需提前 3 个工作日申请。证据来自本地知识库 company_leave_policy.md，全程本地推理，数据不出域。",
        seconds=22,
        progress=0.55,
        clock="02:40",
    )
    frames += scene_chat(
        Image,
        ImageDraw,
        ImageFont,
        "涉密文档可以用哪些 AI 工具？",
        "kb_search",
        "涉密场景仅允许 PrivateLocalAgent 或已批准的本地模型；禁止把涉密内容发到公有云对话服务。",
        seconds=20,
        progress=0.68,
        clock="03:20",
    )
    frames += scene_features(Image, ImageDraw, ImageFont)
    frames += scene_architecture(Image, ImageDraw, ImageFont)
    frames += scene_closing(Image, ImageDraw, ImageFont)

    print(f"[info] frames={len(frames)} duration~{len(frames)/FPS:.1f}s")
    encode(frames, OUT_MP4)
    size = OUT_MP4.stat().st_size if OUT_MP4.exists() else 0
    print(f"[ok] {OUT_MP4}  size={size}  ~{len(frames)/FPS:.0f}s")


if __name__ == "__main__":
    main()
