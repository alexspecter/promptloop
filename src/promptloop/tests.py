import unittest
from unittest.mock import MagicMock, patch, ANY
import json
import sys
import io

# Import your modules
import functions
import engine

class TestFunctions(unittest.TestCase):
    
    # --- Testing History Management ---
    def test_trim_messages_basic(self):
        """Test that history is trimmed correctly to the limit."""
        system = {"role": "system", "content": "sys"}
        msgs = [system]
        
        # Add 10 turns (20 messages)
        for i in range(10):
            msgs.append({"role": "user", "content": f"u{i}"})
            msgs.append({"role": "assistant", "content": f"a{i}"})
            
        # Max turns 2 => should keep System + last 4 messages (2 turns)
        trimmed = functions.trim_messages(msgs, max_turns=2)
        
        self.assertEqual(len(trimmed), 5) # 1 sys + 2 user + 2 assistant
        self.assertEqual(trimmed[0], system)
        self.assertEqual(trimmed[-1]["content"], "a9")

    def test_trim_messages_short_history(self):
        """Test that short history is left untouched."""
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        trimmed = functions.trim_messages(msgs, max_turns=5)
        self.assertEqual(len(trimmed), 2)

    def test_trim_messages_invalid_input(self):
        """Test robustness against bad max_turns inputs."""
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        
        # logic: max_turns < 1 becomes 1. 
        # 1 turn = 2 messages (user+assistant). 
        # Our input only has 1 user message, so it fits within 1 turn.
        # Result should be [Sys, User] (len 2).
        trimmed = functions.trim_messages(msgs, max_turns=0) 
        self.assertEqual(len(trimmed), 2)

    # --- Testing JSON Parsing ---
    def test_parse_json_clean(self):
        """Test parsing valid JSON."""
        valid = '{"key": "value", "list": [1, 2]}'
        self.assertEqual(functions.parse_json_response(valid), {"key": "value", "list": [1, 2]})

    def test_parse_json_markdown(self):
        """Test extracting JSON from markdown code blocks."""
        markdown = """
        Here is the code you asked for:
        ```json
        {
            "status": "success",
            "data": null
        }
        ```
        """
        result = functions.parse_json_response(markdown)
        self.assertEqual(result["status"], "success")

    def test_parse_json_failure(self):
        """Test that invalid JSON raises a ValueError."""
        broken = "This is just text, no JSON here."
        with self.assertRaises(ValueError):
            functions.parse_json_response(broken)

    # --- Testing Token Counting ---
    def test_count_tokens(self):
        """Test the token counter wrapper."""
        mock_tokenizer = MagicMock()
        # Simulate encoding a string into 3 tokens
        mock_tokenizer.encode.return_value = [1, 2, 3]
        
        count = functions.count_tokens(mock_tokenizer, "test text")
        self.assertEqual(count, 3)


class TestEngine(unittest.TestCase):
    
    # --- Testing Chat Loop (Streaming) ---
    @patch("engine.load")
    @patch("engine.stream_generate")  # Mock the streaming generator
    @patch("engine.mx.clear_cache")
    def test_run_chat_stream_flow(self, mock_clear_cache, mock_stream_generate, mock_load):
        """
        Tests the standard chat loop with streaming enabled.
        """
        # 1. Setup Mock Model & Tokenizer
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.model_max_length = 1000
        mock_tokenizer.encode.side_effect = lambda x: [1] * len(x.split())
        mock_tokenizer.apply_chat_template.return_value = "Mock Prompt"
        
        mock_load.return_value = (mock_model, mock_tokenizer)

        # 2. Setup Stream Generator Output
        chunk1 = MagicMock(); chunk1.text = "Hello"
        chunk2 = MagicMock(); chunk2.text = " World"
        mock_stream_generate.return_value = iter([chunk1, chunk2])
        
        # 3. Setup User Input
        input_mock = MagicMock(side_effect=["Hi AI", "exit"])

        # 4. Run the Engine
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            engine.run_chat(
                system_prompt={"role": "system", "content": "You are a test bot."},
                model_path="fake/path",
                input_fn=input_mock,
                stream=True,
                verbose=False
            )
        
        # 5. Assertions
        
        # Verify calls
        mock_stream_generate.assert_called()
        mock_clear_cache.assert_called()
        
        # Verify history was updated
        call_args = mock_tokenizer.apply_chat_template.call_args
        passed_messages = call_args[0][0]
        
        # NOTE: passed_messages is a reference to the list. 
        # Since the engine appends the assistant response AFTER applying the template,
        # 'passed_messages' will effectively contain: [System, User("Hi AI"), Assistant("Hello World")]
        
        # Check that the USER message is in the second to last spot
        self.assertEqual(passed_messages[-2]["content"], "Hi AI")
        # Check that the ASSISTANT message was appended at the end
        self.assertEqual(passed_messages[-1]["content"], "Hello World")
    # --- Testing Chat Loop (Non-Streaming) ---
    @patch("engine.load")
    @patch("engine.generate") # Mock the standard generator
    def test_run_chat_no_stream(self, mock_generate, mock_load):
        """Test the non-streaming path calls generate() instead of stream_generate()."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.model_max_length = 1000
        mock_tokenizer.encode.return_value = [1]
        mock_load.return_value = (MagicMock(), mock_tokenizer)
        
        mock_generate.return_value = "Full Response"
        input_mock = MagicMock(side_effect=["Hi", "exit"])
        
        engine.run_chat(
            system_prompt={},
            model_path="fake",
            input_fn=input_mock,
            stream=False,
            verbose=False
        )
        
        mock_generate.assert_called()

    # --- Testing Edge Cases: Context Limit ---
    @patch("engine.load")
    def test_context_limit_error(self, mock_load):
        """Test that the engine detects prompts that are too large."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.model_max_length = 10 
        # Make a prompt that counts to 20 tokens (over the limit of 10)
        mock_tokenizer.encode.side_effect = lambda x: [0] * 20
        mock_tokenizer.apply_chat_template.return_value = "Long Prompt"
        
        mock_load.return_value = (MagicMock(), mock_tokenizer)
        
        # Input that triggers the overflow, then exit
        input_mock = MagicMock(side_effect=["Huge Input", "exit"])
        
        # Capture stdout to verify the error message print
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            engine.run_chat(
                system_prompt={"role": "system", "content": ""},
                model_path="fake",
                input_fn=input_mock,
                verbose=False
            )
            
            output = fake_out.getvalue()
            self.assertIn("Prompt too large", output)
            self.assertIn("Clearing history", output)

    # --- Testing Edge Cases: Model Load Failure ---
    @patch("engine.load")
    def test_model_load_failure(self, mock_load):
        """Test that loading errors are raised correctly."""
        mock_load.side_effect = Exception("Disk error")
        
        with self.assertRaises(RuntimeError) as cm:
            engine.run_chat(
                system_prompt={},
                model_path="bad/path",
                input_fn=MagicMock()
            )
        self.assertIn("Failed to load model", str(cm.exception))

if __name__ == "__main__":
    unittest.main()