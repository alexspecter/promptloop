from typing import Callable, Union, Optional, List, Dict
import mlx.core as mx
from mlx_lm import load, generate, stream_generate
from mlx_lm.sample_utils import make_sampler

from .types import MessageHistory
from .history import trim_messages
from .tokens import TokenTimer
from .guard import MemoryGuardian, get_memory_stats

SAMPLING_PROFILES = {
    "balanced": {"temp": 0.6, "top_p": 1.0, "top_k": -1},
    "creative": {"temp": 0.8, "top_p": 0.9, "top_k": -1},
    "precise": {"temp": 0.2, "top_p": 0.95, "top_k": -1},
    "strict": {"temp": 0.0, "top_p": 1.0, "top_k": -1},
}


def run_chat(
    system_prompt: Union[dict, str],
    model_path: str,
    input_fn: Callable[[], str],
    *,
    # Core Settings
    max_tokens: int = 2048,
    history_limit: int = 10,
    stream: bool = True,
    expect_json: bool = False,
    verbose: bool = True,
    # UI Settings
    wait_message: str = "",
    response_prefix: str = "",
    output_callback: Optional[Callable[[str], None]] = None,
    # --- NEW: CUSTOM CONTROLS ---
    exit_keywords: List[str] = ["exit", "quit"],  # Default if nothing passed
    # Safety Settings
    use_guardian: bool = False,
    max_input_tokens: int = 4000,
    # Sampling
    profile: str = "balanced",
    temp: Optional[float] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, str]]:

    def emit(text: str):
        if output_callback:
            output_callback(text)
        else:
            print(text, end="", flush=True)

    # 1. Setup
    if isinstance(system_prompt, str):
        system_prompt = {"role": "system", "content": system_prompt}

    if verbose:
        emit(f"Loading model: {model_path}...\n")

    # Use the 'trash bag' syntax to safely handle variable returns from MLX
    model, tokenizer, *_ = load(model_path)

    guardian = MemoryGuardian() if use_guardian else None
    messages: MessageHistory = [system_prompt]

    # Resolve Sampling
    defaults = SAMPLING_PROFILES.get(profile, SAMPLING_PROFILES["balanced"])
    final_temp = temp if temp is not None else defaults["temp"]
    final_top_p = top_p if top_p is not None else defaults["top_p"]
    final_top_k = top_k if top_k is not None else defaults["top_k"]

    if verbose:
        emit("Model loaded.\n")

        # --- SMART INSTRUCTION LOGIC ---
        # 1. Format Exit Keywords: "Type 'exit' or 'quit'"
        exit_instr = " or ".join(f"'{k}'" for k in exit_keywords)

        # 2. Detect Sentinel from Input Function Tag
        auto_sentinel = getattr(input_fn, "sentinel_tag", None)
        sentinel_instr = (
            f" (Type '{auto_sentinel}' on new line to send)" if auto_sentinel else ""
        )

        # 3. Print Clean Message
        emit(f"Type {exit_instr} to stop{sentinel_instr}.\n\n")
        # -------------------------------

    # 2. Master Loop
    try:
        while True:
            try:
                user_input = input_fn()
            except (EOFError, KeyboardInterrupt):
                break

            # --- CUSTOM EXIT CHECK ---
            if not user_input or user_input.lower() in [
                k.lower() for k in exit_keywords
            ]:
                break

            # Input Safety
            if len(user_input) > (max_input_tokens * 5):
                emit(
                    f"⚠️ Input too long (approx {len(user_input) // 4} tokens). Limit is {max_input_tokens}.\n"
                )
                continue

            if wait_message:
                emit(f"{wait_message}\n")

            messages.append({"role": "user", "content": user_input})
            messages = trim_messages(messages, history_limit)

            # Apply Template
            try:
                prompt = tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception as e:
                emit(f"Error applying chat template: {e}\n")
                continue

            sampler = make_sampler(
                temp=final_temp, top_p=final_top_p, top_k=final_top_k
            )
            response_text = ""
            timer = TokenTimer()
            first_chunk = True

            try:
                if stream:
                    timer.start()
                    for response in stream_generate(
                        model,
                        tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        sampler=sampler,
                    ):
                        if guardian:
                            guardian.check()

                        if first_chunk:
                            if response_prefix:
                                emit(response_prefix)
                            first_chunk = False

                        chunk = response.text
                        emit(chunk)
                        response_text += chunk
                        timer.tick()

                    mem_stats = get_memory_stats() if use_guardian else ""
                    emit(f"\n{timer.report()} {mem_stats}\n{'-' * 40}\n")
                else:
                    if response_prefix:
                        emit(response_prefix)
                    response_text = generate(
                        model,
                        tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        sampler=sampler,
                        verbose=False,
                    )
                    emit(f"{response_text}\n{'-' * 40}\n")

            except MemoryError as e:
                emit(f"\n\n🛑 {e}\nStopping generation.\n")
                break

            messages.append({"role": "assistant", "content": response_text})

    finally:
        mx.clear_cache()
        if verbose:
            emit("\n🧹 Memory cache cleared.\n")

    return messages
