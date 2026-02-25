from .types import MessageHistory


def trim_messages(messages: MessageHistory, max_turns: int) -> MessageHistory:
    if max_turns < 1:
        max_turns = 1

    if len(messages) <= 1:
        return messages

    system_prompt = messages[0]
    conversation_history = messages[1:]

    trimmed_history = conversation_history[-(max_turns * 2) :]

    return [system_prompt] + trimmed_history
