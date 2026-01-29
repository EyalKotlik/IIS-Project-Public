"""
LLM Client Module
==================

Central wrapper for LLM calls using LangChain + OpenAI.
Provides caching, budget tracking, structured outputs, and error handling.
"""

import logging
import time
from typing import Any, Dict, Optional, Type, TypeVar, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from .llm_config import LLMConfig, get_config
from .llm_exceptions import (
    LLMAPIKeyMissingError,
    LLMBudgetExceededError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMParsingError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from .llm_budget import BudgetTracker
from .llm_cache import LLMCache

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Wrapper for LLM API calls with caching, budget tracking, and error handling.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.
        
        Args:
            config: Optional LLMConfig instance. If None, loads from environment/secrets.
        """
        self.config = config or get_config()
        
        # Validate API key
        if not self.config.api_key:
            raise LLMAPIKeyMissingError()
        
        # Initialize components
        self.budget_tracker = BudgetTracker(cache_dir=self.config.cache_dir)
        self.cache = LLMCache(
            cache_dir=self.config.cache_dir,
            enabled=self.config.cache_enabled
        )
        
        # Initialize LangChain ChatOpenAI
        self._llm = None
        
        logger.info(f"LLM Client initialized with model={self.config.model}, "
                   f"cache_enabled={self.config.cache_enabled}")
    
    def get_llm(self) -> ChatOpenAI:
        """
        Get a configured ChatOpenAI instance.
        
        Returns:
            Configured ChatOpenAI instance
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                api_key=self.config.api_key,
                timeout=self.config.timeout_sec,
                max_tokens=self.config.max_output_tokens,
                max_retries=self.config.max_retries,
            )
        
        return self._llm
    
    def _check_budget(self):
        """Check if budget allows for more calls."""
        current_spend = self.budget_tracker.get_total_spend()
        
        if current_spend >= self.config.budget_stop_at_usd:
            raise LLMBudgetExceededError(
                current_spend=current_spend,
                budget_limit=self.config.budget_stop_at_usd
            )
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using tiktoken.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        try:
            import tiktoken
            # Use cl100k_base encoding (for gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to use tiktoken for token estimation: {e}. "
                          f"Falling back to rough approximation.")
            # Fallback: rough approximation (~4 characters per token)
            return len(text) // 4
    
    def call_llm(
        self,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        schema: Optional[Type[T]] = None,
        retry_on_parse_error: bool = True
    ) -> Dict[str, Any]:
        """
        Make an LLM call with caching, budget tracking, and optional structured output.
        
        Args:
            task_name: Name of the task (for logging/tracking)
            system_prompt: System prompt
            user_prompt: User prompt
            schema: Optional Pydantic model for structured output
            retry_on_parse_error: Whether to retry once if parsing fails
            
        Returns:
            Dict containing:
                - result: Parsed result (Pydantic model if schema provided, else string)
                - usage: Dict with input_tokens, output_tokens, estimated_cost_usd
                - cache_hit: Boolean indicating if result was from cache
                
        Raises:
            LLMBudgetExceededError: If budget threshold exceeded
            LLMAPIKeyMissingError: If API key not configured
            LLMTimeoutError: If call times out
            LLMConnectionError: If connection fails
            LLMParsingError: If structured output parsing fails
        """
        # Check budget before making call
        self._check_budget()
        
        # Generate schema name for caching
        schema_name = schema.__name__ if schema else None
        
        # Check cache
        cached = self.cache.get(
            model=self.config.model,
            temperature=self.config.temperature,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name=schema_name
        )
        
        if cached:
            # Record cache hit in budget tracker (no cost)
            self.budget_tracker.record_usage(
                task_name=task_name,
                model=self.config.model,
                input_tokens=cached['input_tokens'],
                output_tokens=cached['output_tokens'],
                cache_hit=True
            )
            
            return {
                "result": cached['response'],
                "usage": {
                    "input_tokens": cached['input_tokens'],
                    "output_tokens": cached['output_tokens'],
                    "estimated_cost_usd": 0.0,  # Cache hits are free
                },
                "cache_hit": True
            }
        
        # Make actual LLM call
        try:
            llm = self.get_llm()
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            logger.info(f"Making LLM call: task={task_name}, model={self.config.model}")
            
            start_time = time.time()
            
            if schema:
                # Structured output using LangChain's with_structured_output
                llm_with_schema = llm.with_structured_output(schema)
                response = llm_with_schema.invoke(messages)
                result = response
            else:
                # Regular text response
                response = llm.invoke(messages)
                result = response.content
            
            elapsed = time.time() - start_time
            
            # Estimate token usage (since we don't have direct access to usage from response)
            # In production, you'd extract this from response metadata if available
            input_tokens = self._estimate_tokens(system_prompt + user_prompt)
            output_tokens = self._estimate_tokens(
                str(result) if schema else result
            )
            
            # Calculate cost
            cost = self.budget_tracker.calculate_cost(
                self.config.model, input_tokens, output_tokens
            )
            
            # Record usage
            self.budget_tracker.record_usage(
                task_name=task_name,
                model=self.config.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_hit=False
            )
            
            # Cache the response
            if schema:
                # Convert Pydantic model to dict for caching
                # Using model_dump() which is available in Pydantic v2+
                cache_response = result.model_dump()
            else:
                cache_response = result
            
            self.cache.put(
                model=self.config.model,
                temperature=self.config.temperature,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response=cache_response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                schema_name=schema_name
            )
            
            logger.info(f"LLM call completed: elapsed={elapsed:.2f}s, "
                       f"tokens={input_tokens}+{output_tokens}, cost=${cost:.6f}")
            
            return {
                "result": result,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost_usd": cost,
                },
                "cache_hit": False
            }
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"LLM call failed: task={task_name}, error={error_type}: {str(e)}")
            
            # Map to our custom exceptions
            if "timeout" in str(e).lower():
                raise LLMTimeoutError(self.config.timeout_sec)
            elif "rate limit" in str(e).lower():
                raise LLMRateLimitError()
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                raise LLMConnectionError(e)
            else:
                # Re-raise as generic LLM error
                raise LLMConnectionError(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about LLM usage and cache.
        
        Returns:
            Dict with budget and cache statistics
        """
        return {
            "budget": self.budget_tracker.get_stats(),
            "cache": self.cache.get_stats(),
            "config": {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "budget_usd": self.config.budget_usd,
                "budget_stop_at_usd": self.config.budget_stop_at_usd,
            }
        }


# Singleton instance for convenience
_client_instance: Optional[LLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """
    Get or create the singleton LLM client instance.
    
    Args:
        config: Optional configuration. Only used on first call.
        
    Returns:
        LLMClient instance
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = LLMClient(config)
    
    return _client_instance


def reset_llm_client():
    """Reset the singleton instance (useful for testing)."""
    global _client_instance
    _client_instance = None
