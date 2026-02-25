PromptLoop
PromptLoop is a high-performance, safety-first wrapper for MLX-LM designed specifically for Apple Silicon (M1/M2/M3/M4).

It abstracts away the complex logic of running local LLMs—memory management, token streaming, history trimming, and system safety—allowing you to build powerful, stable AI tools with just a few lines of code.

⚡️ Key Features
🛡️ Safety & Stability

Memory Guardian: Active "Zero-Tolerance" monitoring. If RAM hits 95% or Swap > 0GB, the engine stops immediately to prevent system freeze.

Input Flood Protection: Automatically rejects massive text pastes (e.g., accidental PDFs) that would crash the tokenizer.

🧠 Smart Control

Sampling Profiles: One-click presets (creative, precise, strict) to instantly change the AI's "brain chemistry."

Headless Bridge: Built-in hooks to pipe output to GUIs (Tkinter, PyQt, Web) without parsing terminal text.

Custom Exit Triggers: Define your own stop words (e.g., ["bye", "quit", "stop"]).

💾 Storage

Chat Export: Built-in utility to save conversation history to clean, readable text files.

📦 Installation
Since this library is designed for local development, install it in Editable Mode. This allows you to tweak the library and see changes instantly.

Bash
git clone https://github.com/yourusername/promptloop.git
cd promptloop
pip install -e .
🛠️ The Master Template
This script demonstrates every capability of the library: profiles, safety, file saving, and custom inputs.

Python
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
            profile="creative",    # Options: balanced, creative, precise, strict
            
            # --- Safety ---
            use_guardian=True,     # Kill if RAM > 95%
            max_input_tokens=4000, # Reject massive inputs
            
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
🎭 Sampling Profiles Index
You can change the AI's "personality" by passing the profile argument to run_chat.

Profile	Temp	Top-P	Best For...
balanced	0.6	1.0	Default. Good mix of coherence and variety.
creative	0.8	0.9	Storytelling. Writes more human-like, varied prose.
precise	0.2	0.95	Editing. Stick to the facts/instructions. Less hallucination.
strict	0.0	1.0	Coding/Math. Deterministic. Always gives the same answer.
🎛️ Understanding Sampling Parameters
If you want to manually tune the AI beyond the profiles, here is what the numbers actually do.

🔥 Temperature (Chaos Level)

Controls the randomness of the next token.

0.0 (Cold): The model always picks the most likely word. Robotic, repetitive, safe.

1.0 (Hot): The model picks from a wider range of words. Creative, unpredictable, human.

Recommended Range: 0.6 - 0.8

🎯 Top-P (Nucleus Sampling)

A "smart filter" that cuts off the least likely words.

1.0 (Off): Considers every possible word in the dictionary.

0.9 (On): Only considers the top 90% most likely words. This removes "gibberish" while keeping creativity high.

Why use it? It prevents the AI from going completely off the rails when using high temperature.

🔢 Top-K (Hard Filter)

Restricts the AI to the top K words.

-1 (Off): Our default. Modern models generally perform better with Top-P than Top-K.

🖥️ Building a GUI (The Bridge Pattern)
PromptLoop is "Headless," meaning it can power a Chatbot GUI without blocking the interface.

The Logic:

Input: Use a Python Queue to pass text from the GUI to the Engine.

Output: Use the output_callback argument to pipe text from the Engine to your window.

Threading: Run run_chat in a separate thread.

Python
# Minimal GUI Example
def start_engine():
    run_chat(
        ...,
        input_fn=my_queue.get,           # Wait for GUI input
        output_callback=my_text_widget.insert # Send text to GUI
    )

⚙️ Manual Parameter Tuning (Power User Mode)

While PromptLoop includes presets, you can override any individual setting by passing it directly to run_chat. When a manual value is provided, it overrides the profile setting for that specific parameter.

Option 1: Overriding a Profile

If you like the creative profile but want it to be even more "chaotic," you can keep the profile's top_p settings but manually boost the temp.

Python
run_chat(
    ...,
    profile="creative",  # Standard Top-P: 0.9
    temp=1.2             # Overrides creative's 0.8 to a much hotter 1.2
)
Option 2: Complete Manual Control

If you want to ignore the presets entirely, simply pass your own values for all three parameters. This effectively bypasses the profile dictionary.

Python
run_chat(
    ...,
    temp=0.75,
    top_p=0.92,
    top_k=50    # Restricts the model to the top 50 most likely words
)
How the Logic Priority Works:

The engine follows a strict hierarchy when determining which value to use:

Manual Input: If temp, top_p, or top_k are provided as arguments, those values are used first.

Profile Selection: If a parameter is not manually provided, the engine looks at the chosen profile.

Default Fallback: If no profile is chosen, the engine defaults to the balanced profile values.