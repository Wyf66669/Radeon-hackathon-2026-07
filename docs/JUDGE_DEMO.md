# 评委视角 · 如何启动 Demo（Track 2 · PrivateLocalAgent）

**Team:** 说干就干  
**PR:** https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40  
**Video:** https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  

> 视频画面 = 下方命令的真实启动流程（`scripts/demo_judge.py` 输出格式）。

---

## 一键评测（与视频完全一致）

在 **Radeon Cloud** JupyterLab → Terminal：

```bash
cd /workspace/Radeon-hackathon-2026-07
git fetch origin track2-private-local-agent
git checkout track2-private-local-agent
git pull origin track2-private-local-agent

export PLA_DATA_ROOT=/workspace/persistence/PrivateLocalAgent
export HF_HOME=/workspace/persistence/huggingface
export HF_ENDPOINT=https://hf-mirror.com

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -q Pillow rapidocr-onnxruntime

python scripts/verify_rocm.py      # cuda_available: True
python scripts/ingest_sample.py
python scripts/demo_judge.py       # ★ 与 Demo 视频同一套模式/问题
```

`demo_judge.py` 会按顺序跑：

| 顺序 | APP_MODE | 问题（脚本内写死，与视频一致） |
|------|----------|--------------------------------|
| 1 | chat | 用三句话解释什么是私有本地 Agent |
| 2 | vision | 解析刚上传的图片（自动生成 `judge_demo_ocr.png`） |
| 3 | productivity | 记住我喜欢简洁中文回答 |
| 4 | enterprise | 涉密文档可以用哪些 AI 工具？ |
| 5 | workflow | 设计工作流：新员工入职要开通VPN、邮箱和知识库权限 |
| 6 | rag | 知识库里有哪些 IT FAQ？ |
| 7 | developer | 如何确认 ROCm 可用？ |
| 8 | multi | 自动路由：请假政策是什么？ |
| 9 | enterprise | 把客户名单发到微信可以吗？（应拦截） |
| 10 | rag | 请假需要提前几天申请？（≈3 个工作日） |

成功标志：终端出现 `[ok] judge demo finished — all modes exercised`。

---

## 可选：Web UI（视频片尾同款）

```bash
export PLA_ALLOW_PUBLIC=1
python scripts/run_cloudflare_tunnel.py
```

打开终端打印的 `https://xxxx.trycloudflare.com`，切换底部模式芯片，可复测上表问题。

---

## 材料

| 项 | 链接 |
|----|------|
| 官方 PR | https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40 |
| Demo 视频 | https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4 |
| 本说明 | `docs/JUDGE_DEMO.md` |
| 安全 | `docs/SECURITY.md` |
