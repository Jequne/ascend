from pydantic_settings import BaseSettings
from pydantic import Field
import json
from pathlib import Path
from typing import List
from third_party_apis.axiom_trade_api.models.auth import AxiomAgentData

class AxiomTradeConfig(BaseSettings):
    agents_file: str = "users_fingerprints.json"

    class Config:
        env_prefix = "USERS_FINGERPRINTS"
        env_file = ".env"

    def load_axiom_api_agents(self) -> List[AxiomAgentData]:
        agents_path = Path(self.agents_file)

        if not agents_path.exists():
            raise FileNotFoundError(
                f"❌ {self.agents_file} not found"
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
            raise ValueError(f"❌ parsing error: {e}")

        except Exception as e:
            raise ValueError(f"❌ loading agents error: {e}")       


class Settings(BaseSettings):
    app_name: str = "Ascend"
    debug: bool = True
    database_url: str = "sqlite:///./ascend.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    )

    class Config:
        env_file = ".env"

    axiom_api_config: AxiomTradeConfig = AxiomTradeConfig()


settings = Settings()