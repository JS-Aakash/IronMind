import logging
import re
from urllib.parse import urlparse
from typing import Optional

logger = logging.getLogger(__name__)


class SovereigntyViolationError(Exception):
    """Raised when an application component attempts to configure or invoke a cloud LLM or external public endpoint."""
    pass


class CloudProviderBlocker:
    """Safeguard preventing cloud AI providers (OpenAI, Anthropic, Gemini, Bedrock, Cohere) from being configured."""

    FORBIDDEN_KEYWORDS = [
        "openai",
        "api.openai.com",
        "anthropic",
        "api.anthropic.com",
        "claude",
        "generativelanguage.googleapis.com",
        "gemini",
        "bedrock",
        "cohere",
        "azure.openai",
    ]

    FORBIDDEN_ENV_VARS = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "COHERE_API_KEY",
        "AZURE_OPENAI_KEY",
    ]

    @classmethod
    def validate_provider(cls, provider_name: str, endpoint_url: Optional[str] = None) -> bool:
        """Validate that the requested provider is an authorized local on-premise engine."""
        prov_clean = (provider_name or "").lower().strip()
        
        # Check provider name
        for kw in cls.FORBIDDEN_KEYWORDS:
            if kw in prov_clean:
                msg = f"SOVEREIGNTY VIOLATION: Cloud AI provider '{provider_name}' is strictly prohibited in Air-Gapped mode."
                logger.error(msg)
                raise SovereigntyViolationError(msg)

        # Check endpoint URL if supplied
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            host = (parsed.hostname or "").lower()
            if host not in ["127.0.0.1", "localhost", "::1", "0.0.0.0"]:
                msg = f"SOVEREIGNTY VIOLATION: Remote model endpoint '{endpoint_url}' violates loopback isolation."
                logger.error(msg)
                raise SovereigntyViolationError(msg)

        return True


class NetworkEgressInterceptor:
    """Intercepts and inspects outbound network socket/HTTP requests to ensure zero external egress."""

    ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}

    @classmethod
    def is_request_allowed(cls, url_or_host: str) -> bool:
        """Return True if target is strictly within the loopback boundary."""
        if not url_or_host:
            return True

        if "://" in url_or_host:
            parsed = urlparse(url_or_host)
            host = parsed.hostname or ""
        else:
            host = url_or_host.split(":")[0]

        host_clean = host.lower().strip()
        if host_clean in cls.ALLOWED_HOSTS:
            return True

        return False
