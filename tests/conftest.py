"""Pytest fixtures and configuration."""

import pytest
from tripmind.tools.registry import default_registry
from tripmind.core.llm import MockProvider
from tripmind.core.agent import ReActAgent


@pytest.fixture
def registry():
    """Provides the active default tool registry."""
    return default_registry


@pytest.fixture
def mock_agent():
    """Provides a ReAct agent configured with deterministic MockProvider."""
    return ReActAgent(provider=MockProvider(), registry=default_registry)
