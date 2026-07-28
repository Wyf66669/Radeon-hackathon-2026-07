#!/usr/bin/env python3
"""Start Doubao-style web UI + Cloudflare quick tunnel (trycloudflare.com)."""

from __future__ import annotations

import os
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.getenv("HTTP_PORT", "7900"))


def _download(url: str, target: Path) -> None:
    """Download with several fallbacks (SSL issues common behind cloud proxies)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    # 1) curl (often works when Python SSL fails)
    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-fsSL", "-o", str(target), url]
        # some lab proxies use self-signed MITM certs
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and target.exists() and target.stat().st_size > 1_000_000:
            return
        r = subprocess.run([curl, "-kfsSL", "-o", str(target), url], capture_output=True, text=True)
        if r.returncode == 0 and target.exists() and target.stat().st_size > 1_000_000:
            return

    wget = shutil.which("wget")
    if wget:
        r = subprocess.run([wget, "--no-check-certificate", "-O", str(target), url], capture_output=True, text=True)
        if r.returncode == 0 and target.exists() and target.stat().st_size > 1_000_000:
            return

    # 2) urllib with unverified SSL context
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=ctx, timeout=120) as resp, target.open("wb") as f:
        shutil.copyfileobj(resp, f)


def ensure_cloudflared() -> str:
    existing = shutil.which("cloudflared")
    if existing:
        return existing

    # common package locations
    for p in ("/usr/local/bin/cloudflared", "/usr/bin/cloudflared"):
        if Path(p).exists():
            return p

    bin_dir = ROOT / ".tools"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / ("cloudflared.exe" if os.name == "nt" else "cloudflared")
    if target.exists() and target.stat().st_size > 1_000_000:
        return str(target)

    urls = []
    if os.name == "nt":
        urls.append(
            "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        )
    else:
        urls.extend(
            [
                "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
                # mirror fallback
                "https://ghproxy.com/https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
            ]
        )

    last_err: Exception | None = None
    for url in urls:
        try:
            print(f"[cloudflare] downloading {url}")
            _download(url, target)
            if os.name != "nt":
                target.chmod(0o755)
            if target.exists() and target.stat().st_size > 1_000_000:
                return str(target)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"[cloudflare] download failed: {exc}")

    raise RuntimeError(
        "无法自动下载 cloudflared。请在终端手动安装后重试：\n"
        "  curl -kL -o .tools/cloudflared "
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64\n"
        "  chmod +x .tools/cloudflared\n"
        f"原始错误: {last_err}"
    )


def wait_health(port: int, seconds: int = 30) -> None:
    import urllib.error

    url = f"http://127.0.0.1:{port}/healthz"
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            time.sleep(1)
    print("[web] health check timeout — continuing anyway")


def main() -> None:
    env = os.environ.copy()
    env["HTTP_HOST"] = "127.0.0.1"
    env["HTTP_PORT"] = str(PORT)

    print(f"[web] starting PrivateLocalAgent studio on http://127.0.0.1:{PORT}")
    web = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "web_http_demo.py")],
        cwd=str(ROOT),
        env=env,
    )
    wait_health(PORT)
    try:
        cf = ensure_cloudflared()
    except Exception as exc:  # noqa: BLE001
        web.terminate()
        raise SystemExit(str(exc)) from exc

    print("[cloudflare] quick tunnel (no login). Public URL prints below.")
    print("[cloudflare] Keep this terminal open while demoing.")
    try:
        subprocess.call([cf, "tunnel", "--url", f"http://127.0.0.1:{PORT}"])
    finally:
        web.terminate()
        try:
            web.wait(timeout=5)
        except Exception:  # noqa: BLE001
            web.kill()


if __name__ == "__main__":
    main()
