"""Tests for the MemoryService factory."""

from unittest.mock import MagicMock, patch

from app.services.memu import create_memory_service
from config.settings import Settings


@patch("app.services.memu.MemoryService")
def test_create_memory_service_returns_instance(mock_cls):
    """Test that create_memory_service returns a MemoryService."""
    mock_cls.return_value = MagicMock()
    settings = Settings(OPENAI_API_KEY="test-key")
    service = create_memory_service(settings)
    mock_cls.assert_called_once()
    assert service is mock_cls.return_value


@patch("app.services.memu.MemoryService")
def test_create_memory_service_default_settings(mock_cls):
    """Test that create_memory_service works with default Settings."""
    mock_cls.return_value = MagicMock()
    service = create_memory_service()
    mock_cls.assert_called_once()
    assert service is mock_cls.return_value


@patch("app.services.memu.MemoryService")
def test_create_memory_service_with_overrides(mock_cls):
    """Test that create_memory_service passes optional config overrides."""
    mock_cls.return_value = MagicMock()
    settings = Settings(OPENAI_API_KEY="test-key")
    create_memory_service(
        settings,
        memorize_config={"some_option": True},
        retrieve_config={"another_option": 42},
    )
    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["memorize_config"] == {"some_option": True}
    assert call_kwargs["retrieve_config"] == {"another_option": 42}
