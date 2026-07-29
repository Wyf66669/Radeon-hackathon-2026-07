## Summary

- **Track:** 2 — Private / local AI agents  
- **Team:** 说干就干  
- **GitHub:** Wyf66669  
- **Project:** PrivateLocalAgent — privacy-first office agent with local RAG, tool calling, planning, session memory, workflow auto-config, and image OCR on **AMD Radeon GPU + ROCm**

### Highlights

- **Six official example apps** + default chat + vision OCR (`docs/SIX_APPS.md`, `docs/VISION.md`, `docs/WORKFLOW_AND_APPS.md`)  
- Dual LLM backends: `local_transformers` (ROCm) and OpenAI-compatible API  
- Chroma + MiniLM private knowledge base; specialist modes force grounded `kb_search` when needed  
- Multi-agent orchestrator with specialist agents + office workflows + skill scaffolding (real files)  
- **Requirement → local workflow/app YAML → export** Dify-like / LangChain-like / YAML / JSON  
- Local **image-text OCR** upload & parse (RapidOCR), data stays on device  
- Doubao-style web UI + Cloudflare tunnel demo (`scripts/run_cloudflare_tunnel.py`)  
- Privacy guard + optional audit trail for enterprise use  
- ROCm verify + latency bench scripts for scoring evidence  

### How to run (Radeon Cloud)

```bash
cd /workspace/Radeon-hackathon-2026-07
git checkout track2-private-local-agent
source .venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
export PLA_DATA_ROOT=/workspace/persistence/PrivateLocalAgent
export HF_HOME=/workspace/persistence/huggingface
pip install -q Pillow rapidocr-onnxruntime
python scripts/run_cloudflare_tunnel.py
# or open notebooks/private_agent_demo.ipynb → Restart Kernel → Run the single cell
```

Docs: `README.md`, `docs/RADEON_CLOUD_RUN.md`, `docs/ARCHITECTURE.md`, `docs/AMD_ROCM_OPTIMIZATION.md`

**Ops note:** before **2026-07-31 18:00 UTC+8** platform maintenance, run `python scripts/backup_to_persistence.py` and keep code pushed to GitHub (`/workspace/persistence` NFS).

### Demo video

- URL: https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
- Length: ~3.2 minutes (v2 visuals)  
- Shows: Cloud ready → ROCm verify → Notebook UI → RAG `kb_search` Q&A → privacy Q&A → feature grid → architecture → closing

## Test plan

- [ ] `python scripts/verify_rocm.py` shows GPU/HIP  
- [ ] Web UI or notebook reaches `ready` and chat works  
- [ ] Ask “请假需要提前几天申请？” in RAG mode → grounded answer  
- [ ] “设计工作流：…” writes `data/workflows/*.yaml` and exports  
- [ ] Upload an image in 图文解析 mode → OCR text returned  
- [ ] Optional: `python scripts/demo_six_apps.py` succeeds  
