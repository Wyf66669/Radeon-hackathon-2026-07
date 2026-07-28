# 开发者生产力 · 本地助手说明（示例）

## 本地仓库约定
- 入口：`app.py`、`notebooks/private_agent_demo.ipynb`
- 验证 GPU：`python scripts/verify_rocm.py`
- 测速：`python scripts/bench_rocm.py`
- 配置：`configs/default.yaml` 中 `backend: local_transformers`

## 常见开发问题
### Q：如何确认 ROCm 可用？
运行 `scripts/verify_rocm.py`，应看到 `cuda_available: True` 与 Radeon 设备名。

### Q：模型下载到哪里？
默认 Hugging Face 缓存：`/root/.cache/huggingface`（大文件不建议堆满 `/workspace`）。

### Q：如何交接环境？
可触发「开发者交接工作流」：检查 GPU 要求、文件列表、知识库状态并写入交接事实。

### Q：依赖安装失败怎么办？
使用项目 `.venv`，并设置 `HF_ENDPOINT=https://hf-mirror.com` 后再安装/拉模型。
