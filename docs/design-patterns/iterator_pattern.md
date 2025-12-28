# Iterator Pattern

The **Iterator Pattern** is a behavioral design pattern that lets you traverse elements of a collection without exposing its underlying representation (list, stack, tree, etc.).

In Python, this pattern is largely built into the language via protocols like `__iter__` and `__next__`, loops (`for x in y`), and generators (`yield`).

## Core Concept

### Analogy
Think of a TV remote's "Next Channel" button. You just press "Next" to see the next channel. You don't need to know if the channels are stored in an array, a linked list, or a tree inside the TV's memory. The remote (Iterator) handles the traversal logic.

## Learning Example: Pythonic Iterator (Generators)

Instead of the classic GoF class structure (which is verbose), Python uses generators for elegant iteration.

```python
# Concrete Aggregate (Iterable)
class Library:
    def __init__(self):
        self.books = ["Book A", "Book B", "Book C"]

    # This IS the Iterator Pattern in Python
    # It returns a generator (which follows the Iterator protocol)
    def __iter__(self):
        for book in self.books:
            yield book

# Client Usage
lib = Library()

# The 'for' loop implicitly uses the iterator
for book in lib:
    print(book)
```

## Agent Space Example: Async Streaming

Your `BaseAgent.stream()` method effectively uses the **Async Iterator Pattern** to handle streaming tokens from the LLM.

```python
# agent/agents/base.py
async def stream(self, user_msg: str, ...):
    # handler.stream_events() returns an ASYNC ITERATOR
    async for event in handler.stream_events():
        if isinstance(event, AgentStream):
            # Yield allows the caller to consume one token at a time
            # without waiting for the full response
            yield event.delta
```

### Benefits
1.  **Memory Efficiency**: Streaming 10,000 search results one by one (lazy loading) instead of loading all into RAM.
2.  **Encapsulation**: Hides whether the data comes from a list, a database cursor, or a network stream.
3.  **Responsiveness**: In UI applications, displaying the first token immediately improves perceived performance.


