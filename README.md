# PromptLoop

A high-performance, safety-first wrapper for **MLX-LM** designed for Apple Silicon (M1/M2/M3/M4).

PromptLoop abstracts away the complex logic of running local LLMs — memory management, token streaming, LoRA adapters, MCP tool calling, history trimming, and system safety — allowing you to build powerful, stable AI tools with just a few lines of code.

---

## ⚡️ Features

### 🛡️ Safety & Stability
- **Memory Guardian** — Active monitoring with configurable RAM/Swap thresholds. If RAM hits 95% or Swap exceeds the limit, the engine stops immediately to prevent system freeze.
- **Input Flood Protection** — Automatically rejects massive text pastes (e.g., accidental PDFs) that would crash the tokenizer.
- **Clean Exit Handling** — Built-in signal handlers prevent zombie processes on `Ctrl+C`.

### 🧠 Smart Control
- **Sampling Profiles** — One-click presets (`creative`, `precise`, `strict`, `balanced`) to instantly change the model's behavior.
- **Custom Exit Triggers** — Define your own stop words (e.g., `["bye", "quit", "save"]`).
- **Headless Bridge** — Built-in `output_callback` hook to pipe output to GUIs (Tkinter, PyQt, Web) without parsing terminal text.

### 🔌 LoRA Adapter Support
- Load any LoRA fine-tuned adapter alongside a base model with a single `adapter_path` argument.
- Works in both `run_chat()` (interactive) and `run_one_shot()` (single-turn) modes.

### 🛠️ MCP Tool Calling (Model Context Protocol)
- Give your local LLM access to external tools using the **FastMCP** standard.
- The engine automatically detects tool calls in the model's output, executes them, and feeds results back into the conversation.
- Bridge any FastMCP server with one function: `mcp_to_promptloop()`.

### 💾 Storage
- **Chat Export** — Built-in utility to save conversation history to clean, readable text files.

### 🔢 Performance Tracking
- **Token Timer** — Real-time tokens-per-second (TPS) reporting after each generation.

---

## 📦 Installation

This library is designed for local development on Apple Silicon. Install with `uv`:

```bash
git clone https://github.com/yourusername/promptloop.git
cd promptloop
uv sync
```

Or install in editable mode with pip:

```bash
pip install -e .
```

**Requirements:** Python ≥ 3.10, macOS with Apple Silicon.

---

## 🛠️ The Master Template

This script demonstrates every core capability of the library: profiles, safety, file saving, custom inputs, and LoRA adapters.

```python
import os
from promptloop import (
    run_chat,
    get_multiline_input,
    configure_input,
    register_signal_handlers
)
from promptloop.storage import save_chat_history

def main():
    # 1. Clean Exit Handling (Prevents zombie processes)
    register_signal_handlers()

    # 2. Setup & Configuration
    model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

    # 3. Custom Input Tool
    # Allows pasting multi-line text. Sends when user types '!!!' on a new line.
    user_tool = configure_input(
        get_multiline_input,
        "\n📝 Paste text (Type '!!!' to send): ",
        sentinel="!!!"
    )

    print(f"🔄 Initializing {model_path}...")

    # 4. The Engine
    try:
        # Returns the full chat history when the session ends
        history = run_chat(
            system_prompt="You are a helpful assistant.",
            model_path=model_path,
            input_fn=user_tool,

            # --- Personality ---
            profile="creative",       # Options: balanced, creative, precise, strict

            # --- LoRA (Optional) ---
            adapter_path=None,         # Path to a LoRA adapter directory

            # --- Safety ---
            use_guardian=True,         # Kill if RAM > 95%
            max_input_tokens=4000,     # Reject massive inputs

            # --- Control ---
            exit_keywords=["bye", "save", "quit"],
            stream=True,

            # --- UI Polish ---
            wait_message="\n(🧠 Thinking...)",
            response_prefix="\n🤖 Llama: "
        )

        # 5. Save Workflow
        if history:
            save = input("\n💾 Save session? (y/n): ")
            if save.lower() == 'y':
                save_chat_history(history, filename="~/Desktop/session.txt")
                print("✅ Saved to Desktop.")

    except Exception as e:
        print(f"\n[!] Critical Error: {e}")

if __name__ == "__main__":
    main()
```

---

## 🔌 MCP Tool Calling Example

Give your local model access to external tools using the Model Context Protocol:

```python
from mcp import FastMCP
from promptloop import run_chat, register_signal_handlers
from promptloop.mcp_tools import mcp_to_promptloop

# 1. Define your tools
mcp = FastMCP("MyTools")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is 22°C and sunny."

@mcp.tool()
def search_docs(query: str) -> str:
    """Search internal documentation."""
    return f"Found 3 results for '{query}'."

# 2. Bridge to PromptLoop
tools, handler = mcp_to_promptloop(mcp)

# 3. Run with tools
register_signal_handlers()
run_chat(
    system_prompt="You are an assistant with access to tools. Use them when needed.",
    model_path="mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    input_fn=input,
    tools=tools,
    tool_handler=handler,
    stream=True,
)
```

When the model decides to call a tool, the engine will:
1. Parse the tool call JSON from the model's output.
2. Execute the matching tool function.
3. Inject the result back into the conversation.
4. Re-prompt the model for a final answer.

---

## 🔥 One-Shot Mode

For single-turn inference (no chat loop), use `run_one_shot()`:

```python
from promptloop import run_one_shot

response = run_one_shot(
    model_path="mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    system_prompt="You are a code reviewer.",
    user_prompt="Review this function: def add(a, b): return a + b",
    adapter_path=None,  # Optional LoRA adapter
)
print(response)
```

---

## 🎭 Sampling Profiles

Change the model's behavior with a single string:

| Profile      | Temp  | Top-P | Best For                                              |
|:-------------|:-----:|:-----:|:------------------------------------------------------|
| `balanced`   | 0.6   | 1.0   | Default. Good mix of coherence and variety.            |
| `creative`   | 0.8   | 0.9   | Storytelling. More human-like, varied prose.           |
| `precise`    | 0.2   | 0.95  | Editing. Stick to facts/instructions. Less hallucination. |
| `strict`     | 0.0   | 1.0   | Coding/Math. Deterministic. Always the same answer.    |

### Manual Override

Override any individual setting while keeping the rest of a profile:

```python
run_chat(
    ...,
    profile="creative",  # Standard Top-P: 0.9
    temp=1.2             # Override to a much hotter 1.2
)
```

Or bypass profiles entirely with full manual control:

```python
run_chat(
    ...,
    temp=0.75,
    top_p=0.92,
    top_k=50
)
```

**Priority:** Manual arguments → Profile values → `balanced` defaults.

---

## 🖥️ Building a GUI (The Bridge Pattern)

PromptLoop is headless — it can power a GUI without blocking the interface:

```python
import threading
from queue import Queue

gui_queue = Queue()

def start_engine():
    run_chat(
        ...,
        input_fn=gui_queue.get,              # Wait for GUI input
        output_callback=my_text_widget.insert # Send text to GUI
    )

threading.Thread(target=start_engine, daemon=True).start()
```

- **Input:** Use a `Queue` to pass text from the GUI to the engine.
- **Output:** Use `output_callback` to pipe text from the engine to your window.
- **Threading:** Run `run_chat` in a separate thread.

---

## 📖 API Reference

### `run_chat()`

The main interactive chat engine.

| Parameter          | Type                      | Default         | Description                                     |
|:-------------------|:--------------------------|:----------------|:------------------------------------------------|
| `system_prompt`    | `str` or `dict`           | —               | System prompt (auto-wrapped if string).          |
| `model_path`       | `str`                     | —               | HuggingFace repo or local model path.            |
| `input_fn`         | `Callable`                | —               | Function that returns user input.                |
| `max_tokens`       | `int`                     | `2048`          | Max tokens per response.                         |
| `history_limit`    | `int`                     | `10`            | Max conversation turns to keep.                  |
| `stream`           | `bool`                    | `True`          | Stream tokens in real-time.                      |
| `profile`          | `str`                     | `"balanced"`    | Sampling preset.                                 |
| `temp`             | `float` or `None`         | `None`          | Manual temperature override.                     |
| `top_p`            | `float` or `None`         | `None`          | Manual top-p override.                           |
| `top_k`            | `int` or `None`           | `None`          | Manual top-k override.                           |
| `adapter_path`     | `str` or `None`           | `None`          | Path to LoRA adapter directory.                  |
| `tools`            | `list` or `None`          | `None`          | MCP tool schemas for the model.                  |
| `tool_handler`     | `Callable` or `None`      | `None`          | Function to dispatch tool calls.                 |
| `use_guardian`      | `bool`                   | `False`         | Enable Memory Guardian.                          |
| `max_input_tokens` | `int`                     | `4000`          | Max input length before rejection.               |
| `exit_keywords`    | `list[str]`               | `["exit","quit"]` | Words that end the session.                    |
| `wait_message`     | `str`                     | `""`            | Message shown while model generates.             |
| `response_prefix`  | `str`                     | `""`            | Prefix before each response.                     |
| `output_callback`  | `Callable` or `None`      | `None`          | Redirect output to a function (GUI hook).        |
| `verbose`          | `bool`                    | `True`          | Print status messages.                           |

**Returns:** `List[Dict[str, str]]` — The full message history.

### `run_one_shot()`

Single-turn inference. No chat loop.

| Parameter       | Type             | Default  | Description                          |
|:----------------|:-----------------|:---------|:-------------------------------------|
| `model_path`    | `str`            | —        | HuggingFace repo or local path.      |
| `system_prompt` | `str` or `dict`  | —        | System prompt.                       |
| `user_prompt`   | `str`            | —        | The user's input.                    |
| `max_tokens`    | `int`            | `2048`   | Max tokens.                          |
| `adapter_path`  | `str` or `None`  | `None`   | Path to LoRA adapter.                |
| `model`         | `Any` or `None`  | `None`   | Pre-loaded model (avoids reload).    |
| `tokenizer`     | `Any` or `None`  | `None`   | Pre-loaded tokenizer.                |

**Returns:** `str` — The model's response.

### `mcp_to_promptloop(mcp_server)`

Bridges a FastMCP server into PromptLoop.

**Returns:** `(tools, tool_handler)` — A tuple ready to pass into `run_chat()`.

### `save_chat_history(messages, filename)`

Exports a message history list to a formatted text file.

### `configure_input(func, prompt_text, sentinel)`

Pre-configures an input function with baked-in arguments. Attaches the sentinel as a hidden tag for the engine to auto-discover.

### `get_multiline_input(prompt_text, sentinel)`

Collects multi-line input until the sentinel string is entered on a new line.

### `register_signal_handlers()`

Registers `SIGINT` handlers for clean `Ctrl+C` exit behavior.

---

## 🔐 Security

This project follows the **Ironclad Security Protocol**:

- All dependencies are version-pinned in `pyproject.toml` and locked in `uv.lock`.
- No `eval()`, `exec()`, or `shell=True` anywhere in the codebase.
- Pre-commit hooks enforce **Ruff**, **Gitleaks**, **Trivy**, and **Semgrep** on every commit.

---

## 📄 License

MIT