import re


class GuardrailChecker:
    """Validates user queries and agent responses for safety and relevance."""

    BLOCKED_PATTERNS = [
        # Prompt-injection / override attempts
        r"(?i)ignore\s+(?:all\s+|the\s+|any\s+)?(?:previous|prior|earlier|above)?\s*(?:instructions|prompts|rules|guidelines)",
        r"(?i)disregard\s+(?:all\s+|the\s+|previous|prior)?\s*(?:instructions|prompts|rules)",
        r"(?i)forget\s+(?:everything|all|your|the)\s+(?:above|previous|instructions|prompts|rules)",
        r"(?i)you\s+are\s+now\s+",
        r"(?i)pretend\s+to\s+be",
        r"(?i)act\s+as\s+(?!a\s+soc|an?\s+(network|identity|policy|security))",
        r"(?i)reveal\s+(your|the)\s+(system|initial)\s+prompt",
        # Requests for offensive tradecraft
        r"(?i)(give|show|teach|tell)\s+(me\s+)?(the\s+)?(steps|how)\s+to\s+(attack|hack|exploit|breach|bypass)",
        r"(?i)attack\s+steps",
        r"(?i)how\s+to\s+(hack|exploit|bypass|crack|brute[-\s]?force)",
        r"(?i)write\s+(malware|ransomware|a\s+virus|an?\s+exploit)",
    ]

    OFF_TOPIC_KEYWORDS = [
        "recipe", "cooking", "weather forecast", "sports score",
        "write me a poem", "tell me a joke", "dating advice",
    ]

    @classmethod
    def check_input(cls, query: str) -> dict:
        """Check if user input is safe and on-topic. Returns {safe: bool, reason: str|None}."""
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, query):
                return {"safe": False, "reason": "Prompt injection attempt detected."}

        query_lower = query.lower()
        for keyword in cls.OFF_TOPIC_KEYWORDS:
            if keyword in query_lower:
                return {"safe": False, "reason": "Query is not related to security operations."}

        return {"safe": True, "reason": None}

    @classmethod
    def check_output(cls, response: str) -> dict:
        """Check if agent response is safe to return."""
        sensitive_patterns = [
            r"(?i)my\s+(api|secret)\s+key\s+is",
            r"(?i)password\s*[:=]\s*\S+",
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, response):
                return {"safe": False, "reason": "Response may contain sensitive data."}

        return {"safe": True, "reason": None}
