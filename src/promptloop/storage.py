import os
from typing import List, Dict

def save_chat_history(
    messages: List[Dict[str, str]], 
    filename: str = "chat_history.txt",
    user_prefix: str = "User: ",
    ai_prefix: str = "AI: "
) -> str:
    """
    Exports the chat history to a formatted text file.
    """
    full_path = os.path.abspath(os.path.expanduser(filename))
    
    with open(full_path, "w", encoding="utf-8") as f:
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                continue
                
            if role == "user":
                f.write(f"{user_prefix}\n{content}\n\n")
            elif role == "assistant":
                f.write(f"{ai_prefix}\n{content}\n\n")
            
            f.write("-" * 40 + "\n\n")

    return full_path