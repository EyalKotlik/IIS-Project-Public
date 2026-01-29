"""
LLM Configuration Module
========================

Centralized configuration for LLM integration with OpenAI via LangChain.
Handles secret management, budget controls, and model settings.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    
    # Provider settings
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0  # Deterministic by default
    
    # Timeouts and limits
    timeout_sec: int = 60
    max_output_tokens: Optional[int] = 4096
    max_retries: int = 3
    
    # Budget controls
    budget_usd: float = 20.0  # Total project budget
    budget_stop_at_usd: float = 18.0  # Stop making calls at this threshold
    
    # Caching
    cache_enabled: bool = True
    cache_dir: str = ".cache"
    
    # API credentials
    api_key: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.budget_stop_at_usd > self.budget_usd:
            raise ValueError("budget_stop_at_usd must be <= budget_usd")
        if self.max_output_tokens and self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
    
    def get_redacted_key(self) -> str:
        """Return a redacted version of the API key for logging."""
        if not self.api_key:
            return "None"
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


def load_config_from_env() -> LLMConfig:
    """
    Load LLM configuration from environment variables.
    
    Supports:
    - OPENAI_API_KEY
    - LLM_PROVIDER (default: openai)
    - OPENAI_MODEL (default: gpt-4o-mini)
    - LLM_TEMPERATURE (default: 0)
    - LLM_TIMEOUT_SEC (default: 60)
    - LLM_MAX_OUTPUT_TOKENS (default: 4096)
    - LLM_BUDGET_USD (default: 20)
    - LLM_BUDGET_STOP_AT_USD (default: 18)
    - LLM_CACHE_ENABLED (default: true)
    
    Returns:
        LLMConfig instance with values from environment
    """
    budget_usd = float(os.getenv("LLM_BUDGET_USD", "20.0"))
    # Default stop_at to 90% of budget if not specified
    default_stop_at = budget_usd * 0.9
    budget_stop_at_usd = float(os.getenv("LLM_BUDGET_STOP_AT_USD", str(default_stop_at)))
    
    return LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        timeout_sec=int(os.getenv("LLM_TIMEOUT_SEC", "60")),
        max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096")),
        budget_usd=budget_usd,
        budget_stop_at_usd=budget_stop_at_usd,
        cache_enabled=os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true",
        cache_dir=os.getenv("LLM_CACHE_DIR", ".cache"),
        api_key=os.getenv("OPENAI_API_KEY")
    )


def load_config_from_streamlit_secrets() -> LLMConfig:
    """
    Load LLM configuration from Streamlit secrets.
    
    Falls back to environment variables if secrets are not available.
    
    Returns:
        LLMConfig instance with values from Streamlit secrets or env
    """
    try:
        import streamlit as st
        
        # Try to get config from Streamlit secrets
        secrets = st.secrets
        
        budget_usd = float(secrets.get("LLM_BUDGET_USD", 20.0))
        # Default stop_at to 90% of budget if not specified
        default_stop_at = budget_usd * 0.9
        budget_stop_at_usd = float(secrets.get("LLM_BUDGET_STOP_AT_USD", default_stop_at))
        
        return LLMConfig(
            provider=secrets.get("LLM_PROVIDER", "openai"),
            model=secrets.get("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(secrets.get("LLM_TEMPERATURE", 0.0)),
            timeout_sec=int(secrets.get("LLM_TIMEOUT_SEC", 60)),
            max_output_tokens=int(secrets.get("LLM_MAX_OUTPUT_TOKENS", 4096)),
            budget_usd=budget_usd,
            budget_stop_at_usd=budget_stop_at_usd,
            cache_enabled=str(secrets.get("LLM_CACHE_ENABLED", "true")).lower() == "true",
            cache_dir=secrets.get("LLM_CACHE_DIR", ".cache"),
            api_key=secrets.get("OPENAI_API_KEY")
        )
    except (ImportError, FileNotFoundError, AttributeError):
        # Fall back to environment variables if Streamlit is not available
        # or secrets file doesn't exist
        logger.debug("Streamlit secrets not available, falling back to environment variables")
        return load_config_from_env()


def get_config() -> LLMConfig:
    """
    Get LLM configuration with precedence:
    1. Streamlit secrets (if available)
    2. Environment variables (fallback)
    
    Returns:
        LLMConfig instance
    """
    config = load_config_from_streamlit_secrets()
    
    logger.info(f"LLM Config loaded: provider={config.provider}, "
                f"model={config.model}, temperature={config.temperature}, "
                f"cache_enabled={config.cache_enabled}, "
                f"api_key={config.get_redacted_key()}")
    
    return config
