# 评委视角 · 如何启动 Demo

> 与仓库根目录 **`START_HERE.md`**、网页左侧「评委清单」、Demo 视频使用**同一套 10 条问题**（`src/apps/judge_script.py`）。

**Video:** https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
**PR:** https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40  

---

## 最快：一键脚本

```bash
cd /workspace/Radeon-hackathon-2026-07
git checkout track2-private-local-agent && git pull
bash scripts/start_for_judge.sh
```

然后开网页（与视频同一套推荐问题）：

```bash
PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py
```

打开 `https://xxxx.trycloudflare.com` → 左侧点「评委清单」#1→#10，或底部切换模式后点推荐问题。

---

## 手工三步（与视频片头一致）

```bash
python scripts/verify_rocm.py
python scripts/ingest_sample.py
python scripts/demo_judge.py
```

成功标志：`[ok] judge demo finished — all modes exercised`

完整说明与问题表见 **`START_HERE.md`**。
