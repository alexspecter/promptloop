import time
from typing import List, Dict

def count_tokens(tokenizer, messages: List[Dict[str, str]]) -> int:
    """
    Estimates the total tokens in the message history using the tokenizer.
    """
    if not hasattr(tokenizer, "apply_chat_template"):
        # Fallback for simple tokenizers
        text = " ".join(m["content"] for m in messages)
        return len(tokenizer.encode(text))

    try:
        # Use the official chat template for accuracy
        prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        return len(tokenizer.encode(prompt))
    except Exception:
        # Fallback if template fails
        text = " ".join(m["content"] for m in messages)
        return len(tokenizer.encode(text))


class TokenTimer:
    """
    A simple stopwatch to track generation speed (Tokens Per Second).
    """
    def __init__(self):
        self.start_time = None
        self.token_count = 0

    def start(self):
        """Starts the timer."""
        self.start_time = time.time()

    def tick(self):
        """Increments token count. Call this every time a chunk arrives."""
        if self.start_time is None:
            self.start()
        self.token_count += 1

    def report(self) -> str:
        """Calculates tokens per second (TPS) and returns a formatted string."""
        if self.start_time is None or self.token_count == 0:
            return ""
        
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return ""
            
        tps = self.token_count / elapsed
        return f"({tps:.2f} tokens/sec)"