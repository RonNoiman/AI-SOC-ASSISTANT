import pytest
from unittest.mock import patch, MagicMock

from agents.orchestrator import Orchestrator, _keyword_classify
from agents.base import extract_severity, VALID_SEVERITIES, DEFAULT_SEVERITY
from agents.network_agent import NetworkAgent


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


# ── Severity triage ──

def test_extract_severity_parses_leading_line():
    severity, body = extract_severity("SEVERITY: High\n### Summary\nSomething happened.")
    assert severity == "High"
    assert body.startswith("### Summary")
    assert "SEVERITY" not in body


def test_extract_severity_is_case_insensitive():
    severity, _ = extract_severity("SEVERITY: critical\n### Summary\n...")
    assert severity == "Critical"


def test_extract_severity_falls_back_to_default():
    """A response that ignores the format keeps its text and gets a safe default."""
    severity, body = extract_severity("Here is some unstructured analysis.")
    assert severity == DEFAULT_SEVERITY
    assert body == "Here is some unstructured analysis."


@pytest.mark.asyncio
async def test_agent_demo_mode_returns_structured_result():
    """With no LLM client an agent still returns the {response, severity} shape."""
    agent = NetworkAgent(client=None)
    result = await agent.run("Port scan from 10.0.0.5", history=[])
    assert set(result) == {"response", "severity"}
    assert result["severity"] in VALID_SEVERITIES
    assert "### Recommended Actions" in result["response"]


@pytest.mark.asyncio
async def test_orchestrator_handle_includes_severity():
    """orchestrator.handle() surfaces the agent's severity to the API layer."""
    with patch("agents.orchestrator._build_client", return_value=None):
        orch = Orchestrator()
    result = await orch.handle("Suspicious traffic to port 4444", [])
    assert result["agent"] == "network"
    assert result["severity"] in VALID_SEVERITIES
    assert isinstance(result["response"], str) and result["response"]
