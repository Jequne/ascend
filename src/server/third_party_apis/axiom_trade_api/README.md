# Axiom Trade API Client

A Python library for interacting with Axiom Trade API with WebSocket support for real-time data streams.

## Features

- 🔐 **Agent-based authentication** - Use multiple user fingerprints with headers, cookies, and proxies
- 🌐 **WebSocket streaming** - Real-time price updates and pair information
- 📊 **REST API endpoints** - Access historical data, pair info, and token data
- 🔄 **Auto-reconnection** - Automatic WebSocket reconnection with configurable retry logic
- 🎯 **Callback system** - Register multiple callbacks for different WebSocket rooms
- 🔗 **Async/await** - Full asyncio support for concurrency

## Installation

For current project, the library is part of the codebase:
```python
from axiom_trade_api import AxiomTradeClient, AxiomAgentData
```

For future standalone usage, see `pyproject.toml` configuration.

## Quick Start

```python
import asyncio
from axiom_trade_api import AxiomTradeClient, AxiomAgentData

async def main():
    # Create client
    client = AxiomTradeClient()
    
    # Prepare agent with user fingerprint
    agent = AxiomAgentData.create_with_flat_params(
        auth_refresh_token="your_refresh_token",
        auth_access_token="your_access_token",
        user_agent="your_user_agent"
    )
    
    # Add agent and connect
    client.add_agents([agent])
    client.connect_websocket()
    
    # Register callback for SOL price updates
    client.on_sol_price(lambda data: print(f"SOL Price: {data['content']}"))
    
    # Or use context manager
    async with client:
        await asyncio.sleep(10)  # Listen for updates
    
    # Manual cleanup
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage Examples

### Multiple Agents with SOCKS5 Proxies

```python
agents = [
    AxiomAgentData.create_with_flat_params(
        auth_refresh_token="token1",
        auth_access_token="access1",
        user_agent="user_agent1",
        proxy="socks5://proxy1:port"
    ),
    AxiomAgentData.create_with_flat_params(
        auth_refresh_token="token2",
        auth_access_token="access2",
        user_agent="user_agent2",
        proxy="socks5://proxy2:port"
    ),
]

client.add_agents(agents)
```

### WebSocket Subscriptions

```python
# Register callbacks using decorator-style
@client._wsocket.on("sol_price")
async def handle_sol_price(data):
    print(data)

# Or register directly
client.on_sol_price(handle_sol_price)
```

### REST API Calls

```python
# Get chart data
response = await client.pair_chart_v2(
    pair_address="9YSb1BiRemmSZ6RRiCSuoabLvFWDV2xbHd8Jkp8D1fpJ",
    open_trading=1776845468694,
    last_transaction_time=1776850433201
)
```

## Architecture

### Core Components

- **AxiomTradeClient** - High-level facade for all operations
- **AxiomTradeWebsocket** - WebSocket connection and message dispatch
- **AuthManager** - Token refresh and validation lifecycle
- **AxiomTradeEndpoints** - REST API endpoint helpers
- **AxiomAgentData** - Agent fingerprint abstraction (user agent, cookies, proxy)

### Agent Pattern

The library uses an Agent pattern where each "agent" represents a unique user fingerprint with:
- Custom headers
- Authentication cookies
- Optional SOCKS5 proxy

This enables:
- Anti-detection strategies across multiple APIs
- Load balancing across different proxies
- Fallback mechanisms when some agents fail

## Testing

Run tests from the library directory:

```bash
python -m axiom_trade_api.tests.test_client
```

## Future: Standalone Library

This library is currently part of the main project. When ready to publish as a standalone package:

1. Extract to separate repository
2. Create `pyproject.toml` with dependencies
3. Publish to PyPI
4. Update imports in parent project

Current `pyproject.toml` scaffold is available for migration.

## Dependencies

- `curl_cffi` - HTTP/WebSocket with browser impersonation
- `pydantic` - Data validation and settings management
- `asyncio` - Async/await support (built-in)

## License

[Your License Here]
