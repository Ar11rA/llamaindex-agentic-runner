# Singleton Pattern

The **Singleton Pattern** is a creational design pattern that lets you ensure that a class has only one instance, while providing a global access point to this instance.

In Python, this is often idiomatically implemented using modules or decorators like `@lru_cache` rather than the classic GoF class structure with a private constructor.

## Project Example 1: Settings

We use `functools.lru_cache` to create a singleton for our application settings. This ensures we parse environment variables only once and share the same configuration object throughout the application lifecycle.

```python:agent/config/settings.py
@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
```

## Project Example 2: Database Manager

The `DatabaseManager` is instantiated as a module-level global variable. In Python, modules are singletons by nature, so importing `db_manager` in multiple files results in referencing the exact same instance.

```python:agent/config/database.py
class DatabaseManager:
    """Manages database connections, memory instances, and workflow states."""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        # ... state ...

# Single instance - initialized via FastAPI lifespan
db_manager = DatabaseManager()
```

### Benefits in this Project
1.  **Resource Management**: We only want one database connection pool (`db_manager`) shared across the entire app, rather than opening new connections for every request.
2.  **Performance**: Parsing the `.env` file and validating settings (`get_settings()`) is done once, improving startup time and access speed.
3.  **Consistency**: Global state (like configuration) remains consistent across all modules.

