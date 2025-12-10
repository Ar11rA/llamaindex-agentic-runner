# Adapter Pattern

The **Adapter Pattern** is a structural design pattern that converts the interface of a class into another interface that clients expect. It allows classes with incompatible interfaces to work together.

## Core Concept

### Analogy
A power adapter lets you plug a US device (2 flat prongs) into a European socket (2 round holes). The adapter translates between incompatible interfaces.

### When to Use
Use Adapter when you need to integrate code **you don't own** (third-party libraries, legacy systems) with your application's expected interface.

| Scenario | Solution |
|----------|----------|
| You own both classes | Just refactor one to match the other. No pattern needed. |
| You own the client, not the library | **Adapter**: Wrap the library to match your interface. |

---

## Learning Example: Payment Processing

```python
# 1. The interface YOUR code expects
class PaymentProcessor:
    def pay(self, amount: float) -> bool:
        ...

# 2. A THIRD-PARTY library with a DIFFERENT interface
# You cannot modify this - it's from `pip install stripe`
class StripeAPI:
    def create_charge(self, cents: int, currency: str) -> dict:
        # Returns {"status": "succeeded", ...}
        ...

# 3. The Adapter - makes Stripe look like PaymentProcessor
class StripeAdapter(PaymentProcessor):
    def __init__(self, stripe: StripeAPI):
        self.stripe = stripe

    def pay(self, amount: float) -> bool:
        # Translate: dollars → cents, extract status
        result = self.stripe.create_charge(int(amount * 100), "usd")
        return result["status"] == "succeeded"

# 4. Client code works with the standard interface
def checkout(processor: PaymentProcessor, total: float):
    if processor.pay(total):
        print("Payment successful!")

# Usage
stripe = StripeAPI()
adapter = StripeAdapter(stripe)
checkout(adapter, 49.99)  # Works!
```

---

## Agent Space Example: Custom LLM Integration

Imagine integrating a custom on-premises LLM that doesn't follow LlamaIndex's interface.

### The Problem
Your on-prem LLM has this interface:
```python
class OnPremLLM:
    def generate_text(self, prompt: str, max_tokens: int) -> dict:
        # Returns {"output": "...", "tokens_used": 42}
```

But LlamaIndex expects:
```python
class LLM:
    def complete(self, prompt: str) -> CompletionResponse:
        ...
```

### The Solution: Adapter

```python
from llama_index.core.llms import LLM, CompletionResponse

class OnPremLLMAdapter(LLM):
    """Adapts OnPremLLM to LlamaIndex's LLM interface."""
    
    def __init__(self, on_prem_client: OnPremLLM):
        self._client = on_prem_client

    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        # Translate interface
        result = self._client.generate_text(
            prompt, 
            max_tokens=kwargs.get("max_tokens", 256)
        )
        
        # Convert to LlamaIndex's expected response type
        return CompletionResponse(text=result["output"])

# Usage - seamless integration
on_prem = OnPremLLM(endpoint="http://internal-llm:8080")
adapter = OnPremLLMAdapter(on_prem)

agent = ResearchAgent(llm=adapter)  # Works with LlamaIndex!
```

---

## Project Reference

The `as_tool()` method in `BaseAgent` is a lightweight adapter:

```python
# agent/agents/base.py
def as_tool(self) -> Callable[..., Any]:
    async def agent_tool(input: str) -> str:
        return await self.run(input)
    return agent_tool
```

It adapts the full `BaseAgent` interface to a simple callable function interface that LlamaIndex tools expect.

