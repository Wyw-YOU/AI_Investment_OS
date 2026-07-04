"""Tests for LLM adapter (mocked, no real API calls)."""
import json
from unittest.mock import patch, MagicMock
from app.services.llm_adapter import LLMAdapter


class TestLLMAdapter:
    def setup_method(self):
        self.adapter = LLMAdapter(
            api_key="test-key",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
        )

    def test_stats_initial(self):
        assert self.adapter.stats["total_calls"] == 0
        assert self.adapter.stats["total_tokens"] == 0

    def test_base_url_stored(self):
        assert self.adapter.base_url == "https://api.deepseek.com"

    @patch("app.services.llm_adapter.OpenAI")
    def test_client_uses_base_url(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="ok"))]
        mock_response.usage = MagicMock(total_tokens=10)
        mock_client.chat.completions.create.return_value = mock_response

        self.adapter._client = None  # reset
        self.adapter.generate("test")
        mock_openai_cls.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.deepseek.com",
        )

    @patch("app.services.llm_adapter.OpenAI")
    def test_generate_returns_content(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="analysis result"))]
        mock_response.usage = MagicMock(total_tokens=150)
        mock_client.chat.completions.create.return_value = mock_response

        result = self.adapter.generate("Analyze stock 600519")
        assert result["content"] == "analysis result"
        assert result["tokens"] == 150
        assert result["model"] == "deepseek-chat"

    @patch("app.services.llm_adapter.OpenAI")
    def test_generate_json(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"score": 0.85}'))]
        mock_response.usage = MagicMock(total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_response

        result = self.adapter.generate_json("Return JSON")
        assert result == {"score": 0.85}

    @patch("app.services.llm_adapter.OpenAI")
    def test_retry_on_failure(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            Exception("Rate limit"),
            Exception("Rate limit"),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content="ok"))],
                usage=MagicMock(total_tokens=50),
            ),
        ]

        adapter = LLMAdapter(api_key="test", base_url="https://api.deepseek.com", max_retries=3, base_delay=0.01)
        result = adapter.generate("test")
        assert result["content"] == "ok"

    @patch("app.services.llm_adapter.OpenAI")
    def test_all_retries_exhausted(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Persistent failure")

        adapter = LLMAdapter(api_key="test", base_url="https://api.deepseek.com", max_retries=2, base_delay=0.01)
        result = adapter.generate("test")
        assert result["content"] == ""
        assert "error" in result
