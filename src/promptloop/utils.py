from typing import Callable


def create_system_prompt(content: str) -> dict:
    """
    Helper to quickly create a system prompt dictionary.
    Usage: system = create_system_prompt("You are a helpful AI.")
    """
    return {"role": "system", "content": content}


# src/promptloop/utils.py


def configure_input(
    input_func: Callable = input, prompt_text: str = ">>> ", **kwargs
) -> Callable[[], str]:
    """
    Wraps an input function with a custom prompt string.

    Args:
        input_func: The tool to use (input or get_multiline_input)
        prompt_text: The text to show user
        **kwargs: Extra settings (like sentinel="END") passed to the input_tool
    """

    def wrapped_input() -> str:
        # Passes prompt_text as the first argument, and any other settings
        return input_func(prompt_text, **kwargs)

    return wrapped_input
