from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field
import json
from pathlib import Path
from typing import List, Optional
import logging


def logging_configuration():
    FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"

    # file_handler = logging.FileHandler(filename="./app/logs.txt", encoding="utf-8")
    # file_handler.setLevel(level=logging.WARNING)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        format=FORMAT,
        handlers=[
            # file_handler, 
            stream_handler
            ],
        level=logging.INFO
    )

class AxiomTradeConfig(BaseSettings):
    agents_file_json: Optional[str] = "axiom_users_fingerprints.json"
    agents_file_txt: Optional[str] = "axiom_users_fingerprints.txt"

    class Config:
        env_prefix = "USERS_FINGERPRINTS"
        env_file = ".env"
        extra = "ignore"

    def _check_users_fingerprints_file_path(self, agents_path: Path):
        agents_path = Path(self.agents_file_json)

        if not agents_path.exists():
            raise FileNotFoundError(
                f"❌ {self.agents_file_json} not found"
            )
        return agents_path

    def load_axiom_api_agents(self) -> List:
        from third_party_apis.axiom_trade_api.models.auth import AxiomAgentData

        agents_path = self._check_users_fingerprints_file_path(
           self.agents_file_json
           )
        
        try:
            with open(agents_path, 'r', encoding="utf-8") as f:
                agents_data = json.load(f)

            if isinstance(agents_data, list):
                agents = [AxiomAgentData(**agent) for agent in agents_data]

            else:
                agents = [AxiomAgentData(**agents_data)]

            print(f"✅ loaded {len(agents)} agents from {agents_path}") 
            return agents

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"❌ parsing error: {e}")

        except Exception as e:
            raise Exception(f"❌ loading agents error: {e}")     


class Settings(BaseSettings):
    app_name: str = "Ascend"
    debug: bool = True
    database_url: str = "sqlite:///./ascend.db"
    database_async_url: str = "sqlite+aiosqlite:///./ascend.db"
    """Перец для хэша API-ключей (рекомендуется задать в .env на проде)."""
    api_key_pepper: str = ""
    """Секрет для вызова POST /api/v1/admin/keys (заголовок X-Admin-Secret)."""
    admin_secret: str = "supersecret"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://localhost:1420"
        ]
    )

    class Config:
        env_file = ".env"
        extra = "ignore"

    axiom_api_config: AxiomTradeConfig = AxiomTradeConfig()
    logging_configuration()


settings = Settings()