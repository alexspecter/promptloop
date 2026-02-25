from typing import Optional, Any, Union  # Added Union
import mlx.core as mx
from mlx_lm import load, generate


def run_one_shot(
    model_path: str,
    system_prompt: Union[dict, str],  # Now accepts dict OR str
    user_prompt: str,
    max_tokens: int = 2048,
    adapter_path: Optional[str] = None,
    model: Optional[Any] = None,
    tokenizer: Optional[Any] = None,
) -> str:

    # --- AUTO-FORMATTER ---
    # If the user passed a plain string, wrap it automatically.
    if isinstance(system_prompt, str):
        system_prompt = {"role": "system", "content": system_prompt}
    # ----------------------

    # Only load if not provided
    if model is None or tokenizer is None:
        model, tokenizer, *_ = load(model_path, adapter_path=adapter_path)

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
    if model is None:
        mx.clear_cache()

    return response
