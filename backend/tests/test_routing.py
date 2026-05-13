import pytest
from unittest.mock import patch, MagicMock

from agents.orchestrator import Orchestrator, _keyword_classify


@pytest.fixture
def orchestrator():
    """Build an Orchestrator whose internal client is a mock (no real LLM calls)."""
    mock_client = MagicMock()
    with patch("agents.orchestrator._build_client", return_value=mock_client):
        orch = Orchestrator()
    yield orch, mock_client


@pytest.mark.asyncio
async def test_classify_network_query(orchestrator):
    orch, mock_client = orchestrator
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "network"
    mock_client.chat.completions.create.return_value = mock_response

    result = await orch.classify_query("What firewall rules block port 22?")
    assert result == "network"


@pytest.mark.asyncio
async def test_classify_identity_query(orchestrator):
    orch, mock_client = orchestrator
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "identity"
    mock_client.chat.completions.create.return_value = mock_response

    result = await orch.classify_query("How do I reset a user's MFA?")
    assert result == "identity"


@pytest.mark.asyncio
async def test_classify_unknown_defaults_via_keyword_fallback(orchestrator):
    """When the LLM returns an unknown label, we fall back to keyword classification."""
    orch, mock_client = orchestrator
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "unknown_category"
    mock_client.chat.completions.create.return_value = mock_response

    result = await orch.classify_query("Something random with no keywords")
    assert result == "network"


def test_keyword_classify_policy_beats_identity():
    """Policy keywords should win even when the text mentions 'user' or 'account'."""
    text = "Are we allowed to disable a user account during an active incident?"
    assert _keyword_classify(text) == "policy"


def test_keyword_classify_identity():
    text = "50 failed login attempts for user admin from different countries"
    assert _keyword_classify(text) == "identity"


def test_keyword_classify_network_default():
    text = "Multiple failed RDP connections to port 3389 from unknown IPs"
    assert _keyword_classify(text) == "network"
