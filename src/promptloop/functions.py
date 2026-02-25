# functions.py
import json
import re
import sys
import signal
from typing import List, Dict, Optional, Any
import mlx.core as mx
from mlx_lm import load, generate

# === types.py ===
Message = Dict[str, str]
MessageHistory = List[Message]

# === history.py ===


def trim_messages(messages: MessageHistory, max_turns: int) -> MessageHistory:
    """
    Keeps the system prompt (index 0) and the last N turns.
    One turn = 1 user message + 1 assistant message (2 items).
    """
    if max_turns < 1:
        max_turns = 1

    if len(messages) <= 1:
        return messages

    # 1. Separate System Prompt from the rest of the conversation
    system_prompt = messages[0]
    conversation_history = messages[1:]

    # 2. Slice only the conversation history
    # We want the last (max_turns * 2) messages
    trimmed_history = conversation_history[-(max_turns * 2) :]

    # 3. Recombine
    return [system_prompt] + trimmed_history


# === multi_input.py ===
def get_multiline_input(
    sentinel: str = "!!!",
    prompt: str = "--- Paste code below. Type '!!!' on a new line and hit Enter ---",
) -> str:
    print(prompt)
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == sentinel:
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines).strip()


# === one_shot.py ===
def run_one_shot(
    model_path: str,
    system_prompt: dict,
    user_prompt: str,
    max_tokens: int = 2048,
    # optimization: allow passing loaded model to avoid re-loading
    model: Optional[Any] = None,
    tokenizer: Optional[Any] = None,
) -> str:

    # Only load if not provided
    if model is None or tokenizer is None:
        model, tokenizer, *_ = load(model_path)

    messages = [
        system_prompt,
        {"role": "user", "content": user_prompt},
    ]

    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    # Use generate directly
    response = generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens)

    # Clean up only if we loaded the model locally in this function
    # Otherwise, the caller owns the model lifecycle.
    mx.clear_cache()

    return response


# === output.py ===
def parse_json_response(text: str) -> dict:
    """
    Attempts to parse JSON from a string.
    It looks for the first '{' and last '}' to handle markdown blocks.
    """
    try:
        # Fast path: try parsing the whole string
        return json.loads(text)
    except json.JSONDecodeError:
        # Robust path: extract regex
        # Look for content between the first { and the last }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Model did not return valid JSON. Got: {text[:50]}...")


# === signals.py ===
def force_quit(sig, frame):
    print("\n\n[!] Signal received. Force quitting...")
    sys.exit(0)


def register_signal_handlers():
    signal.signal(signal.SIGINT, force_quit)


# === tokens.py ===
def count_tokens(tokenizer, text: str) -> int:
    # Use built-in tokenizer method if available, otherwise generic encode
    if hasattr(tokenizer, "apply_chat_template"):
        return len(tokenizer.encode(text))
    return len(tokenizer.encode(text))
