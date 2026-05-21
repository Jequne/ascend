from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from app.config import settings

client_instance = AxiomTradeClient(
    settings.axiom_api_config.load_axiom_api_agents()
    )

client_instance.connect_websocket()