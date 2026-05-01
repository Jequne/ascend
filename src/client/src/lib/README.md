# Lib Directory Structure

## Overview

The `lib/` directory follows a clear separation of concerns:

```
lib/
├── config/              # Application configuration
│   └── api.js          # API endpoints and settings
├── core/               # Core utilities and infrastructure
│   ├── http/           # HTTP client
│   │   ├── client.js
│   │   └── index.js
│   └── errors/         # Error types and handlers
│       └── index.js
├── api/                # API services (by domain)
│   ├── auth.js         # Authentication API functions
│   └── index.js
├── components/         # Svelte components
│   └── AuthMenu.svelte
├── index.js            # Root barrel export
└── ...other modules
```

## Modules

### `config/api.js`
Central configuration for API communication.

```javascript
import { API_CONFIG, ENDPOINTS } from '$lib/config/api.js';
```

### `core/http/client.js`
Low-level HTTP client with error handling and timeouts.

```javascript
import { httpClient } from '$lib/core/http';

const data = await httpClient('/api/endpoint', {
  method: 'POST',
  headers: { 'Custom': 'header' }
});
```

### `core/errors/index.js`
Custom error types for better error categorization.

```javascript
import { 
  APIError, 
  NetworkError, 
  ValidationError,
  parseErrorMessage 
} from '$lib/core/errors';
```

### `api/auth.js`
Authentication-related API functions.

```javascript
import { validateApiKey } from '$lib/api/auth.js';

const result = await validateApiKey(apiKey);
```

## Import Patterns

### Direct imports (recommended for smaller projects)
```javascript
import { validateApiKey } from '$lib/api/auth.js';
import { parseErrorMessage } from '$lib/core/errors';
```

### Barrel imports from root
```javascript
import { validateApiKey, parseErrorMessage } from '$lib';
```

### Barrel imports from domain
```javascript
import { validateApiKey } from '$lib/api';
```

## Adding New API Functions

### 1. If adding to existing domain (e.g., `auth.js`)
```javascript
// src/lib/api/auth.js
export async function getTokenFeed() {
  return httpClient(ENDPOINTS.tokenFeed, { method: 'GET' });
}
```

### 2. If adding new domain (e.g., `wallet.js`)
```javascript
// src/lib/api/wallet.js
import { httpClient } from '../core/http';
import { ENDPOINTS } from '../config/api.js';

export async function getWalletBalance(address) {
  return httpClient(ENDPOINTS.walletBalance, {
    method: 'GET',
    headers: { 'Address': address }
  });
}
```

Then update `src/lib/api/index.js`:
```javascript
export { validateApiKey } from './auth.js';
export { getWalletBalance } from './wallet.js';
```

And `src/lib/config/api.js`:
```javascript
export const ENDPOINTS = {
  validateKey: '/api/v1/auth/validate-key',
  walletBalance: '/api/v1/wallet/balance'
};
```

## Benefits of This Structure

✅ **Clear separation**: Config → Core → API layers  
✅ **Scalable**: Easy to add new API domains  
✅ **Maintainable**: Each concern in its own place  
✅ **Testable**: Mockable dependencies  
✅ **Flexible**: Use either direct or barrel imports  
✅ **Future-proof**: Ready for additional core utilities (logging, cache, etc.)

## Error Handling Example

```javascript
import { validateApiKey, parseErrorMessage } from '$lib';

try {
  const result = await validateApiKey(key);
} catch (error) {
  const message = parseErrorMessage(error);
  // Show to user
}
```
