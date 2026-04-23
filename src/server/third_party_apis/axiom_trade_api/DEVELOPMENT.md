# Development Guide

This guide explains how to develop, test, and prepare `axiom_trade_api` for future standalone publication.

## Current Status

✅ **Ready for local integration** - Full functionality as part of the parent project
✅ **Ready for extraction** - Proper package structure (`__init__.py`, `pyproject.toml`)
⏳ **Not yet published** - Standalone library setup complete, awaiting publication decision

## Setting Up Development Environment

### Inside Current Project

```bash
cd src/server
source venv/Scripts/activate  # Windows
python -m pytest axiom_trade_api/tests/
```

### Future Standalone Setup

```bash
# Clone the extracted repository
git clone <repo_url>
cd axiom-trade-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black axiom_trade_api
ruff check axiom_trade_api

# Type checking
mypy axiom_trade_api
```

## Project Structure

```
axiom_trade_api/
├── __init__.py                 # Package exports
├── client.py                    # High-level facade (AxiomTradeClient)
├── urls.py                      # API URL constants
│
├── auth/
│   ├── __init__.py
│   └── auth_manager.py          # Token refresh logic
│
├── endpoints/
│   ├── __init__.py
│   ├── ws.py                    # WebSocket handler
│   └── endpoints.py             # REST API endpoints
│
├── models/
│   ├── __init__.py
│   ├── auth.py                  # AxiomAgentData
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── pair_chart_v2.py
│   │   ├── pair_info.py
│   │   ├── token_info.py
│   │   └── dev_tokens_v3.py
│   └── websockets/
│       ├── __init__.py
│       └── subscription_message.py
│
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_auth_manager.py
│   ├── test_endpoints.py
│   └── test_websockets.py
│
├── README.md                    # User documentation
├── DEVELOPMENT.md               # This file
├── pyproject.toml               # Package configuration
├── MANIFEST.in                  # Distribution files
├── LICENSE                      # MIT License
├── py.typed                     # Type hints marker
└── .gitignore                   # Git ignore rules
```

## Key Architecture Decisions

### Agent Pattern
Each "agent" represents a unique user fingerprint:
- Custom headers
- Authentication cookies
- Optional SOCKS5 proxy

This enables anti-detection strategies and load balancing across multiple APIs.

### Callback System
WebSocket messages are dispatched to registered callbacks:
- Multiple callbacks per room supported
- Sync and async callbacks mixed in `_dispatch_message()`
- Automatic error isolation per callback

### High-Level Facade
`AxiomTradeClient` provides clean public API:
- Hides complexity of auth, websocket, endpoints
- Supports both context manager and manual cleanup
- Random agent selection for load balancing

## Testing

### Current Tests
Located in `axiom_trade_api/tests/`:

```bash
python -m axiom_trade_api.tests.test_client           # Full integration test
python -m axiom_trade_api.tests.test_auth_manager     # Auth logic
python -m axiom_trade_api.tests.test_endpoints        # REST endpoints
python -m axiom_trade_api.tests.test_websockets       # WebSocket alone
```

### Adding New Tests

```python
# axiom_trade_api/tests/test_feature.py
import pytest
import asyncio
from ..client import AxiomTradeClient

@pytest.mark.asyncio
async def test_feature():
    client = AxiomTradeClient()
    # Test code
    await client.close()
```

## Publishing to PyPI

### Prerequisites
1. PyPI account (create at https://pypi.org)
2. Publishing tool: `pip install twine`

### Steps

1. **Create separate repository**
   ```bash
   git clone <this_repo> axiom-trade-api
   cd axiom-trade-api
   ```

2. **Update metadata in `pyproject.toml`**
   ```toml
   [project]
   authors = [{name = "Your Name", email = "your.email@example.com"}]
   # Update repository URLs
   ```

3. **Build distribution**
   ```bash
   pip install build
   python -m build
   ```

4. **Upload to PyPI**
   ```bash
   twine upload dist/*
   ```

5. **Verify**
   ```bash
   pip install axiom-trade-api
   ```

### Versioning
Follow [Semantic Versioning](https://semver.org/):
- `0.1.0` - Alpha (current)
- `0.1.x` - Patch fixes
- `0.2.0` - New features (minor bump)
- `1.0.0` - Stable release

Update `__init__.py` and `pyproject.toml` before each release.

## Code Style Guidelines

### Imports
```python
# Order: stdlib, third-party, local
import asyncio
from typing import Optional, Dict

from curl_cffi import AsyncSession
from pydantic import ValidationError

from .models.auth import AxiomAgentData
```

### Type Hints
```python
# Use type hints for all public APIs
async def pair_chart_v2(
    self,
    pair_address: str,
    open_trading: int,
    last_transaction_time: int,
) -> Optional[PairChartV2Response]:
    pass
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use emoji for clarity
logger.info("✅ Operation succeeded")
logger.warning("🟨 Warning condition")
logger.error("❌ Error occurred")
```

### Docstrings
```python
def method(self, param: str) -> dict:
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param: Parameter description
    
    Returns:
        Result description
    
    Raises:
        ValueError: When something is wrong
    """
    pass
```

## Common Issues

### Race Conditions
- Always `await` cancelled asyncio tasks to ensure `finally` blocks execute
- Example fix: [client.py close() method]

### Unhashable Types
- Pydantic models aren't hashable, can't use in `set()`
- Solution: Use `List[Model]` instead

### Log Duplication
- Avoid logging in "check" methods, only in "action" methods
- Example: Don't log in `_is_auth_access_token_valid()`, log in `ensure_validation()`

## Future Enhancements

### When Adding gmgn.ai API
- **Don't** extract base classes yet (YAGNI principle)
- Create `gmgn_trade_api/` as separate package
- Once structure is clear, consider extracting shared code
- Possible shared: agent pattern, auth patterns, base models

### Low Priority
- Add type stubs for runtime introspection
- Add prometheus metrics
- Add request/response logging middleware
- Add CLI interface

## Questions?

For development questions or issues, refer to:
- README.md for usage examples
- Test files for integration patterns
- Type hints in code for API contracts
