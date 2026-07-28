from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]


class AppConfig(BaseModel):
    name: str = "PrivateLocalAgent"
    team: str = "说干就干"
    track: int = 2
    host: str = "0.0.0.0"
    port: int = 7860


class LLMConfig(BaseModel):
    backend: str = "openai_compatible"
    base_url: str = "https://developer.amd.com.cn/radeon/api/v1"
    api_key_env: str = "RADEON_API_KEY"
    model: str = "Qwen3.6-35B-A3B"
    temperature: float = 0.2
    max_tokens: int = 2048
    local_model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    device: str = "cuda"
    dtype: str = "float16"

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, os.getenv("OPENAI_API_KEY", "EMPTY"))


class RAGConfig(BaseModel):
    persist_dir: str = "data/vector_store"
    collection: str = "private_kb"
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 4
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


class AgentConfig(BaseModel):
    max_steps: int = 6
    enable_tools: bool = True
    enable_memory: bool = True
    memory_path: str = "data/memory/session.json"


class PathsConfig(BaseModel):
    upload_dir: str = "data/uploads"
    sample_docs: str = "data/sample_docs"
    generated_projects: str = "data/generated_projects"


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    def resolve(self, relative: str) -> Path:
        path = Path(relative)
        return path if path.is_absolute() else ROOT / path


def load_settings(config_path: str | Path | None = None) -> Settings:
    load_dotenv(ROOT / ".env")
    path = Path(config_path) if config_path else ROOT / "configs" / "default.yaml"
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    return Settings.model_validate(data)
