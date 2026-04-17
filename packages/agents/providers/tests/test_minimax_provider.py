import unittest
from pathlib import Path


class TestMinimaxProviderIntegration(unittest.TestCase):
    """Integration tests for MinimaxProvider"""
    
    CONFIG_PATH = Path.home() / ".config" / "wisadel" / "config.json"

    @classmethod
    def setUpClass(cls):
        """Set up test class - skip if config file not found"""
        if not cls.CONFIG_PATH.exists():
            raise unittest.SkipTest(f"Config file not found at {cls.CONFIG_PATH}")

    def test_call_returns_string(self):
        """Test that __call__ returns a non-empty string"""
        from agents.providers.minimax_provider import MinimaxProvider

        provider = MinimaxProvider()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."}
        ]
        
        response = provider(messages)
        
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_call_with_simple_prompt(self):
        """Test __call__ with a simple prompt"""
        from agents.providers.minimax_provider import MinimaxProvider

        provider = MinimaxProvider()
        
        messages = [
            {"role": "user", "content": "What is 1+1? Answer only with the number."}
        ]
        
        response = provider(messages)
        
        self.assertIsInstance(response, str)
        # Response should contain "2"
        self.assertIn("2", response)


if __name__ == '__main__':
    unittest.main()
