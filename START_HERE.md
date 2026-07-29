# 启动说明 · PrivateLocalAgent

**评委正确打开方式 = Radeon Cloud 的 Notebook（不是本机 127.0.0.1）。**

- **视频：** https://github.com/Wyf66669/Radeon-hackathon-2026-07/releases/download/demo-v1/PrivateLocalAgent_demo.mp4  
- **PR：** https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/40  

---

## 评委怎么启动（推荐）

1. 登录 [Radeon Cloud](https://radeon-global.anruicloud.com/) → **Open Notebook**（JupyterLab）  
2. 左侧文件树打开：

```text
notebooks/visual_no_tunnel.ipynb
```

3. 菜单 **Kernel → Restart Kernel**  
4. 依次运行：
   - **单元格 1** → 等到终端输出 `ready`（加载本地模型）  
   - **单元格 2** → 出现可视化面板  
5. 下拉选择模式，点**推荐问题**（与 Demo 视频同一套）→ **发送**

界面在 Jupyter 页面里，**不需要**再开 `http://127.0.0.1:7900`，也不需要 Cloudflare。

---

## 首次拉代码（若云上还没有仓库）

在 JupyterLab → **Terminal**：

```bash
cd /workspace
export GIT_SSL_NO_VERIFY=true
git clone -b track2-private-local-agent https://github.com/Wyf66669/Radeon-hackathon-2026-07.git
cd Radeon-hackathon-2026-07
export PLA_DATA_ROOT=/workspace/persistence/PrivateLocalAgent
export HF_HOME=/workspace/persistence/huggingface
export HF_ENDPOINT=https://hf-mirror.com
```

然后回到文件树打开 `notebooks/visual_no_tunnel.ipynb`。

---

## 可选：命令行对齐视频

```bash
python scripts/demo_judge.py
```

---

## 本机 Windows（仅开发预览，非评委主路径）

```bat
scripts\start_web.bat
```

打开 http://127.0.0.1:7900  

---

## 与视频对应的 10 条问题

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
