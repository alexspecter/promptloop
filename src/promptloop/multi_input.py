from typing import Callable, Optional


def get_multiline_input(prompt_text: str = "", sentinel: str = "!!!") -> str:
    """
    Collects multi-line input until the sentinel string is entered on a new line.
    """
    print(prompt_text, end="", flush=True)
    lines = []
    while True:
        line = input()
        if line.strip() == sentinel:
            break
        lines.append(line)
    return "\n".join(lines)


def configure_input(
    func: Callable, prompt_text: str, sentinel: Optional[str] = None
) -> Callable[[], str]:
    """
    Pre-configures an input function (baking in arguments).
    Attaches the sentinel as a hidden tag for the engine to discover.
    """

    def wrapper():
        if sentinel:
            return func(prompt_text, sentinel=sentinel)
        return func(prompt_text)

    # --- THE MAGIC TRICK ---
    # Attach the sentinel value to the function itself
    wrapper.sentinel_tag = sentinel

    return wrapper
