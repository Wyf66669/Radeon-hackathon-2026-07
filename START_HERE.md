# 启动说明 · PrivateLocalAgent（评委 / Demo）

视频、CLI、网页测试页使用**同一套问题**（见 `src/apps/judge_script.py`）。

- **视频：** https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
- **PR：** https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40  

---

## 打开什么网页？

| 场景 | 打开这个地址 |
|------|----------------|
| **本机 Windows** | **http://127.0.0.1:7900** |
| **Radeon Cloud + 隧道** | 终端打印的 **`https://xxxx.trycloudflare.com`** |

本机一键（会自动开浏览器）：

```bat
scripts\start_web.bat
```

云上一键网页：

```bash
bash scripts/start_for_judge.sh
PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py
# 然后打开终端里出现的 https://xxxx.trycloudflare.com
```

网页左侧「评委清单」#1→#10 = 视频同款问题。

---

## Radeon Cloud（推荐）

在 JupyterLab → **Terminal** 粘贴：

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

python scripts/verify_rocm.py
python scripts/ingest_sample.py
python scripts/demo_judge.py
```

看到 `[ok] judge demo finished — all modes exercised` 即与视频一致。

### 打开与视频一致的网页测试页

```bash
PLA_ALLOW_PUBLIC=1 python scripts/run_cloudflare_tunnel.py
```

浏览器打开终端里的 `https://xxxx.trycloudflare.com`：

1. 底部模式芯片按视频顺序切换：对话 → 图文 → 生产力 → 企业 → 工作流 → RAG → 开发 → 多代理  
2. 空白页上的**推荐问题**就是视频里的同一句（点一下即发送）  
3. 左侧「评委清单」可按 1→10 逐条点测  

---

## 本地 Windows

```powershell
cd track2-private-local-agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/demo_judge.py
python scripts/web_http_demo.py
# 打开 http://127.0.0.1:7900
```

---

## 与视频对应的 10 条（勿改措辞）

| # | 模式 | 问题 |
|---|------|------|
| 1 | 对话 | 用三句话解释什么是私有本地 Agent |
| 2 | 图文解析 | 解析刚上传的图片 |
| 3 | 个人生产力助手 | 记住我喜欢简洁中文回答 |
| 4 | 企业副驾驶 | 涉密文档可以用哪些 AI 工具？ |
| 5 | 工作流自动化代理 | 设计工作流：新员工入职要开通VPN、邮箱和知识库权限 |
| 6 | 本地知识助理 | 知识库里有哪些 IT FAQ？ |
| 7 | 开发者生产力代理 | 如何确认 ROCm 可用？ |
| 8 | 多代理系统 | 自动路由：请假政策是什么？ |
| 9 | 企业副驾驶 | 把客户名单发到微信可以吗？ |
| 10 | 本地知识助理 | 请假需要提前几天申请？ |
