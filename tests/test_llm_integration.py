"""
Unit tests for LLM integration modules.

Tests cover:
- Configuration loading (env vars, secrets, precedence)
- Budget tracking and enforcement
- Caching behavior (hit/miss)
- Structured output validation
- Error handling
- Mock-based tests (no actual API calls)
"""

import json
import os
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.llm_config import LLMConfig, load_config_from_env, get_config
from app_mockup.backend.llm_budget import BudgetTracker, UsageRecord
from app_mockup.backend.llm_cache import LLMCache
from app_mockup.backend.llm_client import LLMClient, reset_llm_client
from app_mockup.backend.llm_exceptions import (
    LLMAPIKeyMissingError,
    LLMBudgetExceededError,
    LLMConfigurationError,
)
from app_mockup.backend.llm_schemas import (
    ComponentClassificationResult,
    RelationExtractionResult,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_config(temp_cache_dir):
    """Create a mock LLM configuration."""
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.0,
        timeout_sec=30,
        max_output_tokens=1000,
        budget_usd=10.0,
        budget_stop_at_usd=9.0,
        cache_enabled=True,
        cache_dir=temp_cache_dir,
        api_key="sk-test-key-12345678"
    )


# ============================================================================
# Configuration Tests
# ============================================================================

@pytest.mark.unit
class TestLLMConfig:
    """Test LLM configuration loading and validation."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = LLMConfig(api_key="test-key")
        
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.timeout_sec == 60
        assert config.budget_usd == 20.0
        assert config.budget_stop_at_usd == 18.0
        assert config.cache_enabled is True
    
    def test_config_validation_temperature(self):
        """Test temperature validation."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            LLMConfig(api_key="test-key", temperature=-0.5)
        
        with pytest.raises(ValueError, match="Temperature must be between"):
            LLMConfig(api_key="test-key", temperature=2.5)
    
    def test_config_validation_budget(self):
        """Test budget validation."""
        with pytest.raises(ValueError, match="budget_stop_at_usd must be"):
            LLMConfig(
                api_key="test-key",
                budget_usd=10.0,
                budget_stop_at_usd=15.0
            )
    
    def test_config_redacted_key(self):
        """Test API key redaction for logging."""
        config = LLMConfig(api_key="sk-1234567890abcdef")
        redacted = config.get_redacted_key()
        
        assert redacted.startswith("sk-1")
        assert redacted.endswith("cdef")
        assert "567890ab" not in redacted
    
    def test_config_from_env(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "gpt-4o",
            "LLM_TEMPERATURE": "0.5",
            "LLM_BUDGET_USD": "15.0",
        }):
            config = load_config_from_env()
            
            assert config.api_key == "test-key"
            assert config.model == "gpt-4o"
            assert config.temperature == 0.5
            assert config.budget_usd == 15.0


# ============================================================================
# Budget Tracking Tests
# ============================================================================

@pytest.mark.unit
class TestBudgetTracker:
    """Test budget tracking and enforcement."""
    
    def test_budget_tracker_initialization(self, temp_cache_dir):
        """Test budget tracker initialization."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        assert tracker.total_spend_usd == 0.0
        assert len(tracker.records) == 0
    
    def test_cost_calculation_gpt4o_mini(self, temp_cache_dir):
        """Test cost calculation for gpt-4o-mini."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        # 1000 input tokens, 500 output tokens
        cost = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
        
        # Expected: (1000/1M * 0.15) + (500/1M * 0.60)
        expected = (1000 / 1_000_000 * 0.150) + (500 / 1_000_000 * 0.600)
        assert abs(cost - expected) < 0.0001
    
    def test_cost_calculation_gpt4o(self, temp_cache_dir):
        """Test cost calculation for gpt-4o."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        cost = tracker.calculate_cost("gpt-4o", 1000, 500)
        
        # Expected: (1000/1M * 5.00) + (500/1M * 15.00)
        expected = (1000 / 1_000_000 * 5.00) + (500 / 1_000_000 * 15.00)
        assert abs(cost - expected) < 0.0001
    
    def test_record_usage(self, temp_cache_dir):
        """Test recording usage."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        record = tracker.record_usage(
            task_name="test_task",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500,
            cache_hit=False
        )
        
        assert record.task_name == "test_task"
        assert record.model == "gpt-4o-mini"
        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        assert record.total_tokens == 1500
        assert record.cache_hit is False
        assert record.estimated_cost_usd > 0
        
        assert tracker.total_spend_usd == record.estimated_cost_usd
        assert len(tracker.records) == 1
    
    def test_cache_hit_no_cost(self, temp_cache_dir):
        """Test that cache hits don't incur costs."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        record = tracker.record_usage(
            task_name="cached_task",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500,
            cache_hit=True
        )
        
        assert record.estimated_cost_usd == 0.0
        assert tracker.total_spend_usd == 0.0
    
    def test_budget_check(self, temp_cache_dir):
        """Test budget checking."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        # Initially under budget
        assert tracker.check_budget(10.0) is True
        
        # Add some spending
        tracker.record_usage("task1", "gpt-4o-mini", 10000, 5000, False)
        
        # Still under budget
        assert tracker.check_budget(10.0) is True
        
        # Exceed budget
        for _ in range(100):
            tracker.record_usage("task", "gpt-4o", 10000, 5000, False)
        
        assert tracker.check_budget(10.0) is False
    
    def test_usage_persistence(self, temp_cache_dir):
        """Test that usage data persists across instances."""
        # Create tracker and record some usage
        tracker1 = BudgetTracker(cache_dir=temp_cache_dir)
        tracker1.record_usage("task1", "gpt-4o-mini", 1000, 500, False)
        
        spend1 = tracker1.total_spend_usd
        
        # Create new tracker with same cache dir
        tracker2 = BudgetTracker(cache_dir=temp_cache_dir)
        
        # Should load previous data
        assert tracker2.total_spend_usd == spend1
        assert len(tracker2.records) == 1
    
    def test_get_stats(self, temp_cache_dir):
        """Test getting usage statistics."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        # Record some usage
        tracker.record_usage("task1", "gpt-4o-mini", 1000, 500, False)
        tracker.record_usage("task2", "gpt-4o-mini", 2000, 1000, True)  # Cache hit
        
        stats = tracker.get_stats()
        
        assert stats["total_calls"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_hit_rate"] == 0.5
        assert stats["total_spend_usd"] > 0


# ============================================================================
# Caching Tests
# ============================================================================

@pytest.mark.unit
class TestLLMCache:
    """Test LLM response caching."""
    
    def test_cache_disabled(self, temp_cache_dir):
        """Test that disabled cache doesn't store or retrieve."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=False)
        
        # Try to get (should return None)
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        assert result is None
        
        # Try to put (should not error)
        cache.put("gpt-4o-mini", 0.0, "system", "user", {"key": "value"}, 100, 50)
        
        # Try to get again (should still return None)
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        assert result is None
    
    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        assert result is None
    
    def test_cache_hit(self, temp_cache_dir):
        """Test cache hit."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        response = {"answer": "test response"}
        
        # Store in cache
        cache.put("gpt-4o-mini", 0.0, "system", "user", response, 100, 50)
        
        # Retrieve from cache
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        
        assert result is not None
        assert result["cache_hit"] is True
        assert result["response"] == response
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
    
    def test_cache_key_sensitivity(self, temp_cache_dir):
        """Test that cache keys are sensitive to parameters."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        response1 = {"answer": "response 1"}
        response2 = {"answer": "response 2"}
        
        # Store with different parameters
        cache.put("gpt-4o-mini", 0.0, "system1", "user", response1, 100, 50)
        cache.put("gpt-4o-mini", 0.0, "system2", "user", response2, 100, 50)
        
        # Should get different responses
        result1 = cache.get("gpt-4o-mini", 0.0, "system1", "user")
        result2 = cache.get("gpt-4o-mini", 0.0, "system2", "user")
        
        assert result1["response"] == response1
        assert result2["response"] == response2
    
    def test_cache_temperature_sensitivity(self, temp_cache_dir):
        """Test that cache is sensitive to temperature."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        response1 = {"answer": "temp 0.0"}
        response2 = {"answer": "temp 0.5"}
        
        cache.put("gpt-4o-mini", 0.0, "system", "user", response1, 100, 50)
        cache.put("gpt-4o-mini", 0.5, "system", "user", response2, 100, 50)
        
        result1 = cache.get("gpt-4o-mini", 0.0, "system", "user")
        result2 = cache.get("gpt-4o-mini", 0.5, "system", "user")
        
        assert result1["response"] == response1
        assert result2["response"] == response2
    
    def test_cache_schema_sensitivity(self, temp_cache_dir):
        """Test that cache is sensitive to schema name."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        response1 = {"answer": "schema1"}
        response2 = {"answer": "schema2"}
        
        cache.put("gpt-4o-mini", 0.0, "system", "user", response1, 100, 50, schema_name="Schema1")
        cache.put("gpt-4o-mini", 0.0, "system", "user", response2, 100, 50, schema_name="Schema2")
        
        result1 = cache.get("gpt-4o-mini", 0.0, "system", "user", schema_name="Schema1")
        result2 = cache.get("gpt-4o-mini", 0.0, "system", "user", schema_name="Schema2")
        
        assert result1["response"] == response1
        assert result2["response"] == response2
    
    def test_cache_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        # Add some entries
        cache.put("gpt-4o-mini", 0.0, "system1", "user", {"a": 1}, 100, 50)
        cache.put("gpt-4o-mini", 0.0, "system2", "user", {"b": 2}, 100, 50)
        
        stats = cache.get_stats()
        
        assert stats["enabled"] is True
        assert stats["total_entries"] == 2
        assert stats["total_size_bytes"] > 0
    
    def test_cache_clear(self, temp_cache_dir):
        """Test clearing cache."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        # Add entries
        cache.put("gpt-4o-mini", 0.0, "system", "user", {"test": 1}, 100, 50)
        
        # Verify it's there
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        assert result is not None
        
        # Clear cache
        cache.clear()
        
        # Verify it's gone
        result = cache.get("gpt-4o-mini", 0.0, "system", "user")
        assert result is None


# ============================================================================
# Structured Output Schema Tests
# ============================================================================

@pytest.mark.unit
class TestStructuredOutputSchemas:
    """Test structured output Pydantic schemas."""
    
    def test_component_classification_valid(self):
        """Test valid ComponentClassificationResult."""
        result = ComponentClassificationResult(
            sentence_id="s1",
            label="premise",
            confidence=0.85,
            rationale_short="Contains supporting evidence"
        )
        
        assert result.sentence_id == "s1"
        assert result.label == "premise"
        assert result.confidence == 0.85
        assert result.rationale_short == "Contains supporting evidence"
    
    def test_component_classification_confidence_bounds(self):
        """Test confidence score validation."""
        # Valid
        result = ComponentClassificationResult(sentence_id="s1", label="claim", confidence=0.0)
        assert result.confidence == 0.0
        
        result = ComponentClassificationResult(sentence_id="s2", label="claim", confidence=1.0)
        assert result.confidence == 1.0
        
        # Invalid - below 0
        with pytest.raises(Exception):  # Pydantic validation error
            ComponentClassificationResult(sentence_id="s1", label="claim", confidence=-0.1)
        
        # Invalid - above 1
        with pytest.raises(Exception):  # Pydantic validation error
            ComponentClassificationResult(sentence_id="s1", label="claim", confidence=1.1)
    
    def test_relation_extraction_valid(self):
        """Test valid RelationExtractionResult."""
        result = RelationExtractionResult(
            source_id="s2",
            target_id="s1",
            relation_type="support",
            confidence=0.78,
            rationale_short="Provides evidence"
        )
        
        assert result.source_id == "s2"
        assert result.target_id == "s1"
        assert result.relation_type == "support"
        assert result.confidence == 0.78
    
    def test_schema_serialization(self):
        """Test that schemas can be serialized to JSON."""
        result = ComponentClassificationResult(
            sentence_id="s1",
            label="objection",
            confidence=0.90
        )
        
        # Convert to dict
        data = result.model_dump()
        assert data["sentence_id"] == "s1"
        assert data["label"] == "objection"
        assert data["confidence"] == 0.90
        
        # Convert to JSON
        json_str = result.model_dump_json()
        assert "objection" in json_str


# ============================================================================
# LLM Client Tests (with mocks)
# ============================================================================

@pytest.mark.unit
class TestLLMClient:
    """Test LLM client with mocked API calls."""
    
    def test_client_initialization_no_key(self, temp_cache_dir):
        """Test that client raises error without API key."""
        config = LLMConfig(
            cache_dir=temp_cache_dir,
            api_key=None
        )
        
        with pytest.raises(LLMAPIKeyMissingError):
            LLMClient(config)
    
    def test_client_initialization_with_key(self, mock_config):
        """Test successful client initialization."""
        client = LLMClient(mock_config)
        
        assert client.config.model == "gpt-4o-mini"
        assert client.config.temperature == 0.0
        assert client.budget_tracker is not None
        assert client.cache is not None
    
    def test_budget_check_passes(self, mock_config):
        """Test that budget check passes when under limit."""
        client = LLMClient(mock_config)
        
        # Should not raise
        client._check_budget()
    
    def test_budget_check_fails(self, mock_config, temp_cache_dir):
        """Test that budget check fails when over limit."""
        # Create tracker with high spend
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        # Simulate lots of spending
        for _ in range(100):
            tracker.record_usage("task", "gpt-4o", 10000, 5000, False)
        
        client = LLMClient(mock_config)
        client.budget_tracker = tracker
        
        # Should raise budget exceeded error
        with pytest.raises(LLMBudgetExceededError):
            client._check_budget()
    
    @patch('app_mockup.backend.llm_client.ChatOpenAI')
    def test_call_llm_basic(self, mock_chat, mock_config):
        """Test basic LLM call with mocked response."""
        # Setup mock
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.content = "This is a test response"
        mock_instance.invoke.return_value = mock_response
        mock_chat.return_value = mock_instance
        
        client = LLMClient(mock_config)
        
        result = client.call_llm(
            task_name="test_task",
            system_prompt="You are a helpful assistant",
            user_prompt="Test question"
        )
        
        assert result["result"] == "This is a test response"
        assert result["cache_hit"] is False
        assert result["usage"]["estimated_cost_usd"] > 0
    
    @patch('app_mockup.backend.llm_client.ChatOpenAI')
    def test_call_llm_with_cache(self, mock_chat, mock_config):
        """Test that second call uses cache."""
        # Setup mock
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.content = "Cached response"
        mock_instance.invoke.return_value = mock_response
        mock_chat.return_value = mock_instance
        
        client = LLMClient(mock_config)
        
        # First call
        result1 = client.call_llm(
            task_name="test_task",
            system_prompt="System",
            user_prompt="User"
        )
        
        assert result1["cache_hit"] is False
        first_cost = result1["usage"]["estimated_cost_usd"]
        
        # Second call with same parameters
        result2 = client.call_llm(
            task_name="test_task",
            system_prompt="System",
            user_prompt="User"
        )
        
        assert result2["cache_hit"] is True
        assert result2["usage"]["estimated_cost_usd"] == 0.0  # Cache hits are free
        
        # Should only invoke API once
        assert mock_instance.invoke.call_count == 1
    
    def test_get_stats(self, mock_config):
        """Test getting client statistics."""
        client = LLMClient(mock_config)
        
        stats = client.get_stats()
        
        assert "budget" in stats
        assert "cache" in stats
        assert "config" in stats
        assert stats["config"]["model"] == "gpt-4o-mini"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests for the full LLM workflow."""
    
    def test_full_workflow_with_mocks(self, temp_cache_dir):
        """Test full workflow from config to cached response."""
        # Create config
        config = LLMConfig(
            cache_dir=temp_cache_dir,
            api_key="sk-test-key",
            budget_usd=1.0,
            budget_stop_at_usd=0.9
        )
        
        # Create client
        client = LLMClient(config)
        
        # Verify initial state
        assert client.budget_tracker.total_spend_usd == 0.0
        
        # Mock the LLM call
        with patch.object(client, 'get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = "Test response"
            mock_llm.invoke.return_value = mock_response
            mock_get_llm.return_value = mock_llm
            
            # Make first call
            result1 = client.call_llm(
                task_name="integration_test",
                system_prompt="System",
                user_prompt="User"
            )
            
            assert result1["cache_hit"] is False
            
            # Make second call (should hit cache)
            result2 = client.call_llm(
                task_name="integration_test",
                system_prompt="System",
                user_prompt="User"
            )
            
            assert result2["cache_hit"] is True
        
        # Check stats
        stats = client.get_stats()
        assert stats["budget"]["total_calls"] == 2
        assert stats["budget"]["cache_hits"] == 1


# ============================================================================
# Regression Tests
# ============================================================================

@pytest.mark.regression
class TestLLMRegression:
    """Regression tests with golden outputs."""
    
    def test_budget_calculation_golden(self, temp_cache_dir):
        """Test budget calculation against known values."""
        tracker = BudgetTracker(cache_dir=temp_cache_dir)
        
        # Known test case: 1000 input, 500 output with gpt-4o-mini
        cost = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
        
        # Expected: (1000/1M * 0.15) + (500/1M * 0.60) = 0.00045
        expected = 0.00045
        assert abs(cost - expected) < 0.000001
    
    def test_cache_key_determinism(self, temp_cache_dir):
        """Test that cache keys are deterministic."""
        cache = LLMCache(cache_dir=temp_cache_dir, enabled=True)
        
        # Generate key twice with same parameters
        key1 = cache._generate_cache_key(
            "gpt-4o-mini", 0.0, "system", "user", "Schema"
        )
        key2 = cache._generate_cache_key(
            "gpt-4o-mini", 0.0, "system", "user", "Schema"
        )
        
        # Should be identical
        assert key1 == key2
        
        # Different parameters should give different key
        key3 = cache._generate_cache_key(
            "gpt-4o-mini", 0.5, "system", "user", "Schema"
        )
        
        assert key1 != key3
