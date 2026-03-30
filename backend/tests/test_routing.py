import pytest
from unittest.mock import patch, MagicMock

from agents.orchestrator import Orchestrator


@pytest.fixture
def orchestrator():
    with patch("agents.orchestrator.Groq") as mock_groq:
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        orch = Orchestrator()
        orch.client = mock_client
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
async def test_classify_unknown_defaults_to_network(orchestrator):
    orch, mock_client = orchestrator
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "unknown_category"
    mock_client.chat.completions.create.return_value = mock_response

    result = await orch.classify_query("Something random")
    assert result == "network"
