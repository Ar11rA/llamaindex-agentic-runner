# Factory Pattern

The **Factory Pattern** is a creational design pattern that provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.

In this project, we use a **Simple Factory** variant to create Large Language Model (LLM) instances based on configuration. This abstracts the complexity of instantiating different providers (OpenAI, Anthropic, Bedrock, etc.) with their specific credentials and parameters.

## Project Example: `LLMFactory`

The `LLMFactory` class in `agent/config/llm_factory.py` centralizes the creation of LLM objects.

```python:agent/config/llm_factory.py
class LLMFactory:
    """Factory for creating LLM instances based on provider."""

    @classmethod
    def create(
        cls,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        settings: Optional[Settings] = None,
    ) -> LLM:
        """
        Create an LLM instance based on provider.
        """
        settings = settings or get_settings()
        provider = provider or settings.llm_provider
        # ... (default handling)

        logger.info("Creating LLM: provider=%s, model=%s", provider, model)

        match provider:
            case LLMProvider.OPENAI:
                return cls._create_openai(settings, model, temperature)
            case LLMProvider.ANTHROPIC:
                return cls._create_anthropic(settings, model, temperature)
            case LLMProvider.GEMINI_VERTEX:
                return cls._create_gemini_vertex(settings, model, temperature)
            case LLMProvider.BEDROCK:
                return cls._create_bedrock(settings, model, temperature)
            case LLMProvider.COHERE:
                return cls._create_cohere(settings, model, temperature)
            case _ as unreachable:
                _assert_never(unreachable)

    @staticmethod
    def _create_openai(settings: Settings, model: str, temperature: float) -> LLM:
        """Create OpenAI LLM."""
        from llama_index.llms.openai import OpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        return OpenAI(
            model=model,
            temperature=temperature,
            api_base=settings.openai_api_base,
            api_key=settings.openai_api_key,
        )
    
    # ... other creator methods ...
```

### Benefits in this Project
1.  **Decoupling**: Client code (Agents) doesn't need to know how to instantiate specific LLM classes or which environment variables they need.
2.  **Centralization**: All LLM creation logic is in one place, making it easy to add new providers (like adding a new case to the `match` statement).
3.  **Consistency**: Ensures all LLMs are created with the correct global settings (temperature, timeouts, etc.).

