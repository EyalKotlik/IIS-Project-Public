"""
LLM Exception Classes
======================

Custom exceptions for LLM operations to enable better error handling
and user-friendly error messages.
"""


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is invalid or missing."""
    pass


class LLMAPIKeyMissingError(LLMConfigurationError):
    """Raised when API key is not configured."""
    
    def __init__(self, message: str = "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable or add it to .streamlit/secrets.toml"):
        self.message = message
        super().__init__(self.message)


class LLMBudgetExceededError(LLMError):
    """Raised when budget threshold is exceeded."""
    
    def __init__(self, current_spend: float, budget_limit: float):
        self.current_spend = current_spend
        self.budget_limit = budget_limit
        self.message = (
            f"LLM budget exceeded: ${current_spend:.4f} spent, "
            f"limit is ${budget_limit:.4f}. Further LLM calls are disabled."
        )
        super().__init__(self.message)


class LLMRateLimitError(LLMError):
    """Raised when API rate limit is hit."""
    
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        self.message = f"OpenAI rate limit exceeded. Please retry after {retry_after} seconds."
        super().__init__(self.message)


class LLMTimeoutError(LLMError):
    """Raised when LLM call times out."""
    
    def __init__(self, timeout_sec: int):
        self.timeout_sec = timeout_sec
        self.message = f"LLM call timed out after {timeout_sec} seconds."
        super().__init__(self.message)


class LLMParsingError(LLMError):
    """Raised when structured output cannot be parsed."""
    
    def __init__(self, expected_schema: str, raw_response: str = None):
        self.expected_schema = expected_schema
        self.raw_response = raw_response
        self.message = f"Failed to parse LLM response as {expected_schema}"
        if raw_response:
            self.message += f": {raw_response[:200]}..."
        super().__init__(self.message)


class LLMConnectionError(LLMError):
    """Raised when connection to LLM API fails."""
    
    def __init__(self, original_error: Exception = None):
        self.original_error = original_error
        self.message = "Failed to connect to OpenAI API"
        if original_error:
            self.message += f": {str(original_error)}"
        super().__init__(self.message)
