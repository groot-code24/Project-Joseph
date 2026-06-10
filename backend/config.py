from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str
    ddb_path: str = Field(default="./data/novamart.db")
    policy_path: str = Field(default="./data/refund_policy.md")
    model_name: str = Field(default="claude-opus-4-8")
    max_agent_iterations: int = Field(default=8)
    backend_port: int = Field(default=8000)
    allow_all_origins: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": ("../.env", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "protected_namespaces": (),
    }

    def get_policy_text(self) -> str:
        p = Path(self.policy_path)
        if not p.exists():
            p = Path(__file__).parent.parent / "data" / "refund_policy.md"
        return p.read_text(encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
