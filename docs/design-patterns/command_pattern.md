# Command Pattern

The **Command Pattern** is a behavioral design pattern that turns a request into a stand-alone object that contains all information about the request. This allows you to parameterize methods with different requests, queue or log requests, and support undoable operations.

## Core Concept

Instead of calling a method directly:
```python
light.turn_on()
```

You create an object that represents the action:
```python
command = TurnOnLightCommand(light)
command.execute()
```

## The Four Participants

| Role | Responsibility |
|------|----------------|
| **Command** | An interface (e.g., `execute()`) that all concrete commands implement. |
| **Concrete Command** | Implements the Command interface. Binds a specific action to a Receiver. |
| **Receiver** | The object that actually performs the work (e.g., `Light`, `Database`). |
| **Invoker** | Asks the command to execute. Doesn't know what the command does internally. |

---

## Learning Example: Java Swing's `Action` Interface

Java Swing uses the Command Pattern through the `javax.swing.Action` interface. This is one of the cleanest real-world examples of Command Pattern in a mainstream framework.

### The Problem
In a GUI, the same action (e.g., "Save File") can be triggered from multiple places:
- Menu bar: `File → Save`
- Toolbar button: 💾 icon
- Keyboard shortcut: `Ctrl+S`

Without Command Pattern, you'd duplicate the save logic in 3 places.

### The Solution: `Action` as a Command

```java
// 1. Create the Command (Action)
Action saveAction = new AbstractAction("Save", saveIcon) {
    @Override
    public void actionPerformed(ActionEvent e) {
        // The actual "execute" logic
        saveFile();
    }
};

// Set metadata
saveAction.putValue(Action.SHORT_DESCRIPTION, "Save the current file");
saveAction.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("ctrl S"));

// 2. Reuse the SAME command object in multiple places
JMenuItem menuItem = new JMenuItem(saveAction);   // Menu
JButton toolbarBtn = new JButton(saveAction);      // Toolbar
// Keyboard shortcut is auto-registered via ACCELERATOR_KEY
```

### How It's Called (Invocation)

When the user clicks the button, Swing internally calls:
```java
saveAction.actionPerformed(event);
```

The `JButton` (Invoker) doesn't know *what* the action does. It just calls `.actionPerformed()` — the Command's execute method.

### Benefits
1. **Single Source of Truth**: Change the save logic in one place, all triggers update.
2. **Enable/Disable**: Call `saveAction.setEnabled(false)`, and the menu, toolbar, AND keyboard shortcut all disable simultaneously.
3. **Consistent Metadata**: Icon, tooltip, and name are defined once and shared.

---

## When to Use Command Pattern ✅

The pattern pays off when **undo is non-trivial** or when actions need to be **queued/logged**.

### 1. Regenerate Conversation from a Point
User edits message #5 in a 10-message conversation and clicks "Regenerate from here."

```python
class RegenerateFromCommand:
    def __init__(self, conversation_id, from_index):
        self.conversation_id = conversation_id
        self.from_index = from_index
        self.deleted_messages = []  # Captured on execute

    async def execute(self):
        # Capture what we're about to delete
        self.deleted_messages = await db.get_messages_after(
            self.conversation_id, self.from_index
        )
        await db.delete_messages_after(self.conversation_id, self.from_index)
        # ... regenerate new response ...

    async def undo(self):
        # Restore exactly what was deleted
        await db.insert_messages(self.deleted_messages)
```

### 2. Bulk Operations with Single Undo
User selects 50 conversations and clicks "Archive All."

```python
class BulkArchiveCommand:
    def __init__(self, conversation_ids: list):
        self.conversation_ids = conversation_ids

    async def execute(self):
        await db.archive_conversations(self.conversation_ids)

    async def undo(self):
        await db.unarchive_conversations(self.conversation_ids)
```

One "Undo" button reverses 50 operations cleanly.

### 3. Multi-Step Transactions
A single user action triggers 5 DB writes and 2 API calls. If step 4 fails, you need to rollback steps 1-3.

---

## When NOT to Use Command Pattern ❌

For simple operations, Command Pattern is over-engineering.

### 1. Like/Dislike a Response
This is a simple boolean toggle.

```python
# Like
await db.update(response_id, liked=True)

# Unlike (undo)
await db.update(response_id, liked=False)
```

No complex state to capture. A simple API endpoint handles this.

### 2. Delete Single Message
Store the deleted message in a "trash" table. Restore on undo. Simple CRUD, no Command needed.

### 3. Simple Settings Toggle
Enabling/disabling dark mode, notifications, etc. Just flip a boolean in the database.

---

## Summary Table

| Action | Needs Command? | Why? |
|--------|----------------|------|
| Like/Dislike | ❌ No | Simple boolean flip. |
| Delete single message | ❌ No | Store in "trash" table, restore on undo. |
| Regenerate from a point | ⚠️ Maybe | Capturing deleted messages in a Command is cleaner than ad-hoc storage. |
| Bulk archive 50 items | ⚠️ Maybe | One "undo" button that reverses 50 operations. |
| Complex multi-step workflow | ✅ Yes | Need to rollback on failure. |
| GUI actions (Swing-style) | ✅ Yes | Same action triggered from menu, toolbar, keyboard. |

