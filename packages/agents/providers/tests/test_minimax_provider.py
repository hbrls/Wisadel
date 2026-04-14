import os
import unittest


class TestMinimaxProviderIntegration(unittest.TestCase):
    """Integration tests for MinimaxProvider"""

    @classmethod
    def setUpClass(cls):
        """Set up test class with API key from environment"""
        cls.api_key = os.environ.get("WISADEL_MINIMAX_API_KEY")
        cls.model = os.environ.get("WISADEL_MINIMAX_MODEL")
        if not cls.api_key:
            raise unittest.SkipTest("WISADEL_MINIMAX_API_KEY environment variable not set")
        if not cls.model:
            raise unittest.SkipTest("WISADEL_MINIMAX_MODEL environment variable not set")

    def test_call_returns_string(self):
        """Test that __call__ returns a non-empty string"""
        from agents.providers.minimax_provider import MinimaxProvider

        provider = MinimaxProvider(api_key=self.api_key, model=self.model)
        
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

        provider = MinimaxProvider(api_key=self.api_key, model=self.model)
        
        messages = [
            {"role": "user", "content": "What is 1+1? Answer only with the number."}
        ]
        
        response = provider(messages)
        
        self.assertIsInstance(response, str)
        # Response should contain "2"
        self.assertIn("2", response)


if __name__ == '__main__':
    unittest.main()
