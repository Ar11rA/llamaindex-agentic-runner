# Singleton Pattern

The **Singleton Pattern** is a creational design pattern that lets you ensure that a class has only one instance, while providing a global access point to this instance.

In Python, this is often idiomatically implemented using modules or decorators like `@lru_cache` rather than the classic GoF class structure with a private constructor.

## Best Practices: When to Use

### ✅ Good Use Cases (Stateless Infrastructure)
Singletons are perfect for **shared resource pools** or **read-only configuration**.
*   **Database Connections**: Managing a single connection pool prevents exhausting database limits.
*   **Redis/Cache Clients**: Maintaining persistent connections avoids TCP handshake overhead.
*   **Configuration**: Environment variables don't change at runtime; parse them once.
*   **Logging**: All components should write to the same centralized log stream.

### ❌ Anti-Patterns (Avoid Singletons)
Avoid Singletons for **mutable user state** or **request-specific data**.
*   **User Sessions**: Never store `current_user` in a Singleton. In a concurrent server, one user's data could overwrite another's.
*   **Request Context**: Use Context Variables (`contextvars`) instead of Singletons for request-scoped data.

## Implementation Variants

### 1. The Decorator Approach (Used for Settings)
We use `functools.lru_cache` to create a singleton for our application settings. This ensures we parse environment variables only once.

```python:agent/config/settings.py
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    # This runs only once, no matter how many times it's called
    return Settings()
```

### 2. The Module-Level Singleton (Used for Database)
In Python, modules are singletons by nature. Importing `db_manager` in multiple files results in referencing the exact same instance.

```python:agent/config/database.py
class DatabaseManager:
    def __init__(self):
        self._engine = None
        
    async def connect(self):
        # Create the pool once
        self._engine = create_async_engine(...)

# Single instance - initialized via FastAPI lifespan
db_manager = DatabaseManager()
```

### 3. Dependency Injection (Recommended for External Services)
For services like S3 or Redis, combining a global singleton with Dependency Injection (DI) is powerful for testing.

```python
# pseudo-code example
class S3Client:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = boto3.client("s3")
        return cls._instance

# In FastAPI route
async def upload_file(s3: S3Client = Depends(S3Client.get_instance)):
    s3.upload(...)
```

## Project Benefits
1.  **Resource Efficiency**: We share one `AsyncEngine` pool across the entire app, rather than opening new connections for every request.
2.  **Performance**: Configuration parsing happens once at startup.
3.  **Consistency**: Global state (like configuration) remains consistent across all modules.
