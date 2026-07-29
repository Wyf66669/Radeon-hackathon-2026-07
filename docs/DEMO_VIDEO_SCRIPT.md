# Demo Video Script (3–5 min)

Record on Radeon Cloud JupyterLab. **No tunnel needed.**

## Shot list

| Time | What to show | Say (EN or CN) |
|------|----------------|----------------|
| 0:00–0:30 | Profile: Active Instance + AMD GPU Ready | Team 说干就干, Track 2 PrivateLocalAgent on Radeon Cloud |
| 0:30–1:00 | Terminal: `python scripts/verify_rocm.py` | Local ROCm / HIP device visible |
| 1:00–1:20 | Open `notebooks/private_agent_demo.ipynb` | Tunnel-free visual UI inside Jupyter |
| 1:20–2:20 | Run the one cell → wait `ready` + panel | Loading local Qwen on Radeon GPU |
| 2:20–3:20 | Send: “请假需要提前几天申请？” | Shows Tools: kb_search + grounded answer (3 working days) |
| 3:20–4:00 | Send: “涉密文档可以用哪些 AI 工具？” | Privacy: only PrivateLocalAgent / approved local models |
| 4:00–4:30 | Briefly open `src/agent/agent.py` or ARCHITECTURE.md | RAG + tools + local inference |
| 4:30–5:00 | Closing | Code on branch `track2-private-local-agent`, PR title ready |

## Tips

- Zoom browser so chat bubbles and “Tools:” line are readable  
- If model already loaded, skip long wait by reusing kernel after first `ready`  
- Upload to Bilibili/YouTube/Drive → paste link into `docs/PR_BODY.md` and the GitHub PR  

## Submitted video (current)

- File: `demo_assets/PrivateLocalAgent_demo.mp4` (regenerate: `python scripts/generate_demo_video.py`)  
- Version: v2 — 8fps H.264, typed terminal, notebook/chat mocks, progress bar, ~3.2 min  
- Public URL: https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
- Linked in official PR: https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40  
