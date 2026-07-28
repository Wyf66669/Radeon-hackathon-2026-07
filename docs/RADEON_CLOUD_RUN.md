# Radeon Cloud Run Guide (Track 2)

## Primary demo (recommended, no tunnel)

JupyterLab notebook UI — no `rc-tunnel`, no `/proxy`:

```bash
cd /workspace/Radeon-hackathon-2026-07
git pull origin track2-private-local-agent
export HF_ENDPOINT=https://hf-mirror.com
```

1. Open `notebooks/private_agent_demo.ipynb`
2. **Kernel → Restart Kernel**
3. Run the **single** code cell
4. Wait for `ready` + chat panel → click **发送**

Optional: expand KB to ~10k related FAQs first:

```bash
python scripts/generate_kb_faqs.py --n 10000
python scripts/rebuild_kb.py
```

## CLI demo (stable fallback for video)

```bash
cd /workspace/Radeon-hackathon-2026-07
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export HF_ENDPOINT=https://hf-mirror.com

python scripts/verify_rocm.py
python scripts/ingest_sample.py
python scripts/demo_cli.py
```

## Optional HTTP / Gradio (needs tunnel or proxy)

These are **optional**. On this platform, `/proxy/PORT` may 404 and `rc-tunnel` may timeout.

```bash
# HTTP demo
export HTTP_PORT=7900
python scripts/web_http_demo.py
# then: rc-tunnel expose --port 7900

# Gradio
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7880
python app.py
```

## Save credits

Profile → **Destroy Instance** when finished recording.
