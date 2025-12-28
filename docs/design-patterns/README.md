# Design Patterns Documentation

This folder contains documentation for **GoF (Gang of Four) Design Patterns** implemented or referenced in the LlamaIndex Agents project.

## Patterns by Category

### Creational Patterns
| Pattern | Status | Description |
|---------|--------|-------------|
| [**Factory Method**](factory_pattern.md) | ✅ Implemented | Creates LLM instances based on provider configuration |
| [**Singleton**](singleton_pattern.md) | ✅ Implemented | Manages global instances (settings, database manager) |

### Structural Patterns
| Pattern | Status | Description |
|---------|--------|-------------|
| [**Adapter**](adapter_pattern.md) | 📚 Learning | Wraps incompatible interfaces (e.g., custom LLM providers) |
| [**Facade**](facade_pattern.md) | 📚 Learning | Simplifies complex subsystems (e.g., agent orchestration) |
| [**Decorator**](decorator_pattern.md) | 📚 Learning | Adds behavior to objects dynamically (e.g., caching, permissions) |
| [**Composite**](composite_pattern.md) | 📚 Learning | Composes objects into tree structures (e.g., hierarchical teams) |
| [**Bridge**](bridge_pattern.md) | 📚 Learning | Decouples abstraction from implementation (e.g., Agents & Memory Backends) |
| [**Flyweight**](flyweight_pattern.md) | 📚 Learning | Shares common state to save RAM (e.g., System Prompts across sessions) |

### Behavioral Patterns
| Pattern | Status | Description |
|---------|--------|-------------|
| [**Template Method**](template_method_pattern.md) | ✅ Implemented | Defines algorithm skeleton for agents and teams |
| [**Memento**](memento_pattern.md) | ✅ Implemented | Saves/restores workflow state for Human-in-the-Loop |
| [**Observer**](observer_pattern.md) | 📚 Learning | Notifies components of events (e.g., async auditing) |
| [**Command**](command_pattern.md) | 📚 Learning | Encapsulates requests as objects (e.g., undoable actions) |
| [**Strategy**](strategy_pattern.md) | 📚 Learning | Interchangeable algorithms (e.g., response formatting) |
| [**Iterator**](iterator_pattern.md) | ✅ Implemented | Traverses collections (e.g., streaming agent responses) |
| [**State**](state_pattern.md) | 📚 Learning | Alters behavior when internal state changes (e.g., agent moods) |
| [**Chain of Responsibility**](chain_of_responsibility_pattern.md) | 📚 Learning | Passes requests along a chain of handlers (e.g., middleware) |
| [**Mediator**](mediator_pattern.md) | ✅ Implemented | Encapsulates interaction between objects (e.g., Orchestrator Team) |

## Legend

- ✅ **Implemented**: Pattern used in current codebase with examples
- 📚 **Learning**: Pattern not implemented but documented for educational purposes

## Quick Reference

| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| Factory | Create objects without specifying exact class | Multiple similar object types |
| Singleton | Ensure single instance exists | Shared resources (DB, config) |
| Adapter | Make incompatible interfaces work together | Third-party library integration |
| Facade | Simplify complex subsystem | Hide implementation details |
| Decorator | Add behavior to objects dynamically | Cross-cutting concerns |
| Composite | Treat individual objects and compositions uniformly | Tree structures, hierarchies |
| Bridge | Decouple abstraction from implementation | Avoid class explosion (N*M) |
| Flyweight | Share common state | Memory optimization for massive scale |
| Template Method | Define algorithm skeleton | Framework with customizable steps |
| Memento | Save/restore object state | Undo functionality, state persistence |
| Observer | Notify multiple objects of changes | Event-driven systems |
| Command | Encapsulate requests as objects | Undo, queuing, auditing |
| Strategy | Make algorithms interchangeable | Runtime algorithm selection |
| Iterator | Traverse a collection | Hiding underlying data structure |
| State | Alter behavior based on state | Finite State Machines (FSM) |
| Chain of Responsibility | Pass request along a chain | Middleware, multiple handlers |
| Mediator | Centralize object communication | Decoupling complex dependencies |

## Contributing

When adding new patterns:
1. Create a new `.md` file with the pattern name
2. Include: definition, examples, when to use/not use, and project relevance
3. Update this README with the new entry
4. Use consistent formatting with existing docs