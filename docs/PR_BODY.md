# Pull Request Body (English)

Copy this into the GitHub PR against `AMD-DEV-CONTEST/Radeon-hackathon-2026-07`.

**PR title:** `Track 2, 说干就干, PrivateLocalAgent`

**Compare URL:** https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/compare/main...Wyf66669:track2-private-local-agent?expand=1

---

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

### How to run (Radeon Cloud) — same as Demo video

```bash
cd /workspace/Radeon-hackathon-2026-07
git checkout track2-private-local-agent
source .venv/bin/activate
export PLA_DATA_ROOT=/workspace/persistence/PrivateLocalAgent
export HF_HOME=/workspace/persistence/huggingface
export HF_ENDPOINT=https://hf-mirror.com
pip install -q Pillow rapidocr-onnxruntime
python scripts/verify_rocm.py
python scripts/ingest_sample.py
python scripts/demo_judge.py
# optional Web: PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py
```

Docs: `docs/JUDGE_DEMO.md`, `README.md`, `docs/RADEON_CLOUD_RUN.md`, `docs/ARCHITECTURE.md`, `docs/AMD_ROCM_OPTIMIZATION.md`

**Ops note:** before **2026-07-31 18:00 UTC+8** platform maintenance, run `python scripts/backup_to_persistence.py` and keep code pushed to GitHub (`/workspace/persistence` NFS).

### Demo video

- URL: https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
- Length: ~3 minutes · **same prompts/order as `scripts/demo_judge.py`**  
- Shows: verify_rocm → ingest → chat / vision / six apps / privacy block / leave-policy grounded RAG  

## Test plan

- [ ] `python scripts/verify_rocm.py` shows GPU/HIP  
- [ ] `python scripts/demo_judge.py` finishes with `[ok] judge demo finished`  
- [ ] Ask “请假需要提前几天申请？” in RAG → grounded (~3 working days)  
- [ ] “把客户名单发到微信可以吗？” → privacy_guard block  
- [ ] Optional: `PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py`  
