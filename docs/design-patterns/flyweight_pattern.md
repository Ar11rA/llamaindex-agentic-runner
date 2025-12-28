# Flyweight Pattern

The **Flyweight Pattern** is a structural design pattern that lets you fit more objects into the available amount of RAM by sharing common parts of state between multiple objects instead of keeping all of the data in each object.

## Core Concept

### Analogy: Game Assets
In a war game with 1,000,000 soldiers:
- **Heavy State (Shared)**: 3D mesh, textures, sound effects (Same for all soldiers).
- **Unique State (Context)**: XYZ position, health, current weapon.

Instead of loading the 3D mesh 1M times, you load it **once** (Flyweight) and re-use it for every soldier, passing the XYZ position (Context) when drawing.

### When to Use
- You have a huge number of similar objects.
- The objects drain memory.
- Most of the object state can be made extrinsic (passed in).

---

## Learning Example: Text Formatting

A document has 100,000 characters. Storing `font_name`, `font_size`, `is_bold` for *every single character* is wasteful.

```python
# 1. Flyweight (Shared State)
class FontData:
    def __init__(self, name: str, size: int, bold: bool):
        self.name = name
        self.size = size
        self.bold = bold

    def render(self, char: str, position: int):
        # Uses shared font rules + unique char/position
        print(f"Drawing '{char}' at {position} in {self.name} {self.size}pt")

# 2. Flyweight Factory
class FontFactory:
    _cache = {}

    @classmethod
    def get_font(cls, name, size, bold):
        key = (name, size, bold)
        if key not in cls._cache:
            cls._cache[key] = FontData(name, size, bold)
        return cls._cache[key]

# Usage
# We only create 2 font objects in memory, even if we draw 1000 chars
header_font = FontFactory.get_font("Arial", 16, True)
body_font = FontFactory.get_font("Times", 12, False)

# Context (char, pos) is passed in
header_font.render("H", 0)
header_font.render("i", 1)
body_font.render("t", 10)
```

---

## Agent Space Example: Shared System Prompts

Imagine a SaaS platform with 10,000 concurrent user sessions. Every session has a "HelpBot".

### The Problem
If `HelpBot` stores a 5KB System Prompt string in memory for every user, 10,000 users = 50MB of just repeated text strings.

### The Solution: Flyweight

```python
# 1. Flyweight (The Definition)
class AgentDefinition:
    def __init__(self, system_prompt: str, tools: list):
        self.system_prompt = system_prompt  # Heavy data (Shared)
        self.tools = tools

    def run(self, user_msg: str, session_context: dict):
        # Combine shared prompt with unique session context
        print(f"[System]: {self.system_prompt}")
        print(f"[User {session_context['id']}]: {user_msg}")

# 2. Context (The Session)
class UserSession:
    def __init__(self, user_id):
        self.id = user_id
        self.history = []

# Usage
# One heavy object in memory
help_bot_def = AgentDefinition(
    system_prompt="You are a helpful assistant..." * 100, 
    tools=["search", "email"]
)

# Thousands of lightweight session objects
session_a = UserSession("A")
session_b = UserSession("B")

# The Flyweight processes them
help_bot_def.run("Hello", session_a.__dict__)
help_bot_def.run("Help", session_b.__dict__)
```

### Benefits
1.  **Memory Optimization**: Massive reduction in RAM usage for scale.
2.  **Startup Time**: Initialize the heavy definition once.

---

## Flyweight vs Singleton

- **Singleton**: Only **one** instance of a class exists (e.g., one Database Connection).
- **Flyweight**: **Many** instances exist, but they are shared. You might have 5 different `FontData` flyweights shared across 1M characters.


