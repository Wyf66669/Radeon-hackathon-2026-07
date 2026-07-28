# Submission Checklist — Track 2 · PrivateLocalAgent

Team: **说干就干**  
GitHub: **Wyf66669**  
Project: **PrivateLocalAgent**  
Deadline: **2026-08-06 23:59 (UTC+8)**

## PR title (to official repo)

```text
Track 2, 说干就干, PrivateLocalAgent
```

Fork: https://github.com/Wyf66669/Radeon-hackathon-2026-07  
Branch with code: `track2-private-local-agent`  
Upstream: https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07  
PR draft text: `docs/PR_BODY.md`

## Required materials (Track 2)

| Item | Status | Path / note |
|------|--------|-------------|
| Project specification | Done | `docs/PROJECT_SPECIFICATION.md` |
| Architecture | Done | `docs/ARCHITECTURE.md` |
| AMD/ROCm optimization notes | Done | `docs/AMD_ROCM_OPTIMIZATION.md` |
| Source code + README | Done | `src/`, `app.py`, `README.md` |
| Run / reproduce guide | Done | `README.md`, `docs/RADEON_CLOUD_RUN.md` |
| Poster outline | Done | `docs/POSTER_OUTLINE.md` |
| Tunnel-free visual demo | Done | `notebooks/private_agent_demo.ipynb` |
| Multi-agent + workflows + six apps | Done | `src/agent/multi_agent.py`, `docs/SIX_APPS.md`, `scripts/demo_six_apps.py` |
| Development skills (real files) | Done | `src/skills/`, `scripts/run_skill.py` |
| Privacy guard + audit | Done | `src/privacy/` |
| ROCm bench | Done | `scripts/bench_rocm.py` |
| 10k FAQ generator | Done | `scripts/generate_kb_faqs.py`, `docs/KB_10K.md` |
| Demo video (3–5 min) | TODO | See `docs/DEMO_VIDEO_SCRIPT.md` |
| Open PR to official repo | TODO | Use `docs/PR_BODY.md` |

## Verified on Radeon Cloud (2026-07)

- [x] Instance: AMD OneClick Base (ROCm)
- [x] Local Transformers backend on GPU
- [x] CLI demo (`scripts/demo_cli.py`)
- [x] Notebook one-cell visual chat (no tunnel)
- [x] Mandatory `kb_search` + Chinese grounded answers
- [ ] Demo video uploaded + linked in PR
- [ ] PR opened to `AMD-DEV-CONTEST/Radeon-hackathon-2026-07`

## Final submit steps

1. `git pull` on cloud; run notebook visual demo; record 3–5 min video
2. Upload video (Bilibili / YouTube / Drive) and paste URL into `docs/PR_BODY.md`
3. On GitHub: compare `track2-private-local-agent` → open PR to official repo
4. Title: `Track 2, 说干就干, PrivateLocalAgent`
5. Destroy cloud instance after recording

## Contact

Contest email: ai_dev_contests@amd.com
