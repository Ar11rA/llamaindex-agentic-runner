# Strategy Pattern

The **Strategy Pattern** is a behavioral design pattern that defines a family of algorithms, encapsulates each one, and makes them interchangeable. It lets the algorithm vary independently from clients that use it.

## Core Concept

### Analogy
A navigation app lets you choose between driving, walking, or public transit routes. Each "strategy" (algorithm) gets you to the destination, but differently. You can switch strategies without changing the app's core logic.

### When to Use
Use Strategy when:
- You have multiple algorithms for the same task
- You need to switch algorithms at runtime
- You want to isolate algorithm implementation from client code

---

## Learning Example: Payment Methods

```python
from abc import ABC, abstractmethod

# 1. Strategy Interface
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

# 2. Concrete Strategies
class CreditCardStrategy(PaymentStrategy):
    def __init__(self, card_number: str, cvv: str):
        self.card_number = card_number
        self.cvv = cvv

    def pay(self, amount: float) -> bool:
        # Stripe or payment gateway logic
        print(f"Charging ${amount} to card ****{self.card_number[-4:]}")
        return True

class PayPalStrategy(PaymentStrategy):
    def __init__(self, email: str):
        self.email = email

    def pay(self, amount: float) -> bool:
        # PayPal API logic
        print(f"Charging ${amount} via PayPal account {self.email}")
        return True

class CryptoStrategy(PaymentStrategy):
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address

    def pay(self, amount: float) -> bool:
        # Blockchain transaction logic
        print(f"Sending ${amount} worth of crypto to {self.wallet_address}")
        return True

# 3. Context (Client)
class ShoppingCart:
    def __init__(self):
        self.items = []
        self.payment_strategy: PaymentStrategy = None

    def set_payment_strategy(self, strategy: PaymentStrategy):
        self.payment_strategy = strategy

    def checkout(self, total: float) -> bool:
        if not self.payment_strategy:
            raise ValueError("No payment method selected")

        return self.payment_strategy.pay(total)

# 4. Usage - Runtime Strategy Selection
cart = ShoppingCart()

# User chooses credit card
cart.set_payment_strategy(CreditCardStrategy("1234567890123456", "123"))
cart.checkout(99.99)

# Later, user switches to PayPal
cart.set_payment_strategy(PayPalStrategy("user@example.com"))
cart.checkout(49.99)

# Even later, switches to crypto
cart.set_payment_strategy(CryptoStrategy("0x123abc..."))
cart.checkout(199.99)
```

### Benefits
1. **Open/Closed Principle**: Add new payment methods without changing `ShoppingCart`.
2. **Runtime Flexibility**: Switch strategies without code changes.
3. **Testability**: Test payment methods independently.

---

## Agent Space Example: Response Formatting

Different clients (web UI, CLI, API consumers) need responses in different formats. Use Strategy to encapsulate formatting logic.

### The Problem
Without Strategy, formatting logic gets scattered:

```python
class Agent:
    def run(self, query: str, format: str = "text") -> str:
        response = self._get_response(query)

        if format == "json":
            return json.dumps({"response": response})
        elif format == "markdown":
            return f"**Response:**\n{response}"
        elif format == "html":
            return f"<div class='response'>{response}</div>"
        else:
            return response
```

### The Solution: Strategy Pattern

```python
from abc import ABC, abstractmethod

# 1. Strategy Interface
class ResponseFormatter(ABC):
    @abstractmethod
    def format(self, response: str) -> str:
        pass

# 2. Concrete Strategies
class TextFormatter(ResponseFormatter):
    def format(self, response: str) -> str:
        return response

class JSONFormatter(ResponseFormatter):
    def format(self, response: str) -> str:
        return json.dumps({"response": response})

class MarkdownFormatter(ResponseFormatter):
    def format(self, response: str) -> str:
        return f"**Response:**\n{response}"

class HTMLFormatter(ResponseFormatter):
    def format(self, response: str) -> str:
        return f"<div class='response'>{response}</div>"

# 3. Context (Agent)
class Agent:
    def __init__(self):
        self.formatter: ResponseFormatter = TextFormatter()  # Default

    def set_formatter(self, formatter: ResponseFormatter):
        self.formatter = formatter

    async def run(self, query: str) -> str:
        raw_response = await self._get_llm_response(query)
        return self.formatter.format(raw_response)  # Use strategy

# 4. Usage - Runtime Strategy Selection
agent = Agent()

# For web API
agent.set_formatter(JSONFormatter())
response = await agent.run("What is AI?")

# For documentation
agent.set_formatter(MarkdownFormatter())
response = await agent.run("What is AI?")
```

### Benefits in Agent Context
1. **Multi-Client Support**: Same agent serves web UI (HTML), CLI (text), and APIs (JSON).
2. **Extensibility**: Add new formats (XML, YAML) without touching agent logic.
3. **Configuration**: Switch formats based on request headers or user preferences.

---

## Project Reference

Your `LLMFactory` has a strategy-like structure with different provider implementations, but it's not runtime-swappable. A true Strategy pattern would let you change LLM providers at runtime without reinitializing the agent.

---

## Template Method vs Strategy

| Aspect | Template Method | Strategy |
|--------|----------------|----------|
| **Inheritance vs Composition** | Inheritance (subclasses override methods) | Composition (inject algorithms) |
| **Flexibility** | Fixed algorithm structure, customizable steps | Interchangeable algorithms |
| **When to Use** | "Customize these steps in the fixed flow" | "Choose different algorithms for the same task" |
| **Runtime Change** | No (compile-time) | Yes (inject different strategy) |

Template Method: "Here's the skeleton, customize the steps."
Strategy: "Here are different algorithms, pick one at runtime."
