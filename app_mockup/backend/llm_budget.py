"""
Budget Tracking Module
=======================

Tracks token usage and estimated costs for LLM calls.
Persists data to avoid losing budget information across sessions.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


# OpenAI pricing (last verified: January 2026)
# Prices in USD per 1M tokens
# Source: https://openai.com/api/pricing/
# Note: These prices may change. Update regularly or consider fetching from API.
PRICING_PER_MILLION_TOKENS = {
    "gpt-4o-mini": {
        "input": 0.150,  # $0.15 per 1M input tokens
        "output": 0.600,  # $0.60 per 1M output tokens
    },
    "gpt-4o": {
        "input": 5.00,  # $5 per 1M input tokens
        "output": 15.00,  # $15 per 1M output tokens
    },
    "gpt-4": {
        "input": 30.00,
        "output": 60.00,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    },
}


@dataclass
class UsageRecord:
    """Record of a single LLM call."""
    
    timestamp: str
    task_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    cache_hit: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UsageRecord':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BudgetTracker:
    """Tracks LLM usage and enforces budget limits."""
    
    cache_dir: str = ".cache"
    usage_file: str = "llm_usage.json"
    
    # In-memory state
    records: List[UsageRecord] = field(default_factory=list)
    total_spend_usd: float = 0.0
    
    # Thread safety
    _lock: Lock = field(default_factory=Lock, repr=False)
    
    def __post_init__(self):
        """Load existing usage data if available."""
        self._ensure_cache_dir()
        self._load_usage_data()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_usage_path(self) -> str:
        """Get full path to usage file."""
        return os.path.join(self.cache_dir, self.usage_file)
    
    def _load_usage_data(self):
        """Load usage data from file."""
        path = self._get_usage_path()
        
        if not os.path.exists(path):
            logger.info("No existing usage data found, starting fresh")
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.records = [UsageRecord.from_dict(r) for r in data.get('records', [])]
                self.total_spend_usd = data.get('total_spend_usd', 0.0)
                logger.info(f"Loaded usage data: {len(self.records)} records, "
                           f"${self.total_spend_usd:.4f} total spend")
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
    
    def _save_usage_data(self):
        """Save usage data to file."""
        path = self._get_usage_path()
        
        try:
            data = {
                'records': [r.to_dict() for r in self.records],
                'total_spend_usd': self.total_spend_usd,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved usage data to {path}")
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate estimated cost for a call.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Get pricing or use default if model not found
        pricing = PRICING_PER_MILLION_TOKENS.get(model, PRICING_PER_MILLION_TOKENS["gpt-4o-mini"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def record_usage(
        self,
        task_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool = False
    ) -> UsageRecord:
        """
        Record a single LLM call.
        
        Args:
            task_name: Name of the task
            model: Model used
            input_tokens: Input token count
            output_tokens: Output token count
            cache_hit: Whether this was a cache hit
            
        Returns:
            The created usage record
        """
        with self._lock:
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost (cache hits don't incur costs)
            if cache_hit:
                cost = 0.0
            else:
                cost = self.calculate_cost(model, input_tokens, output_tokens)
            
            record = UsageRecord(
                timestamp=datetime.now().isoformat(),
                task_name=task_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=cost,
                cache_hit=cache_hit
            )
            
            self.records.append(record)
            self.total_spend_usd += cost
            
            # Log the usage
            logger.info(
                f"LLM usage recorded: task={task_name}, model={model}, "
                f"tokens={input_tokens}+{output_tokens}={total_tokens}, "
                f"cost=${cost:.6f}, cache_hit={cache_hit}, "
                f"total_spend=${self.total_spend_usd:.4f}"
            )
            
            # Save to disk
            self._save_usage_data()
            
            return record
    
    def get_total_spend(self) -> float:
        """Get total spend across all calls."""
        return self.total_spend_usd
    
    def check_budget(self, budget_limit: float) -> bool:
        """
        Check if current spend is under budget.
        
        Args:
            budget_limit: Budget limit in USD
            
        Returns:
            True if under budget, False if exceeded
        """
        return self.total_spend_usd < budget_limit
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        if not self.records:
            return {
                "total_calls": 0,
                "total_spend_usd": 0.0,
                "total_tokens": 0,
                "cache_hit_rate": 0.0
            }
        
        total_calls = len(self.records)
        cache_hits = sum(1 for r in self.records if r.cache_hit)
        total_tokens = sum(r.total_tokens for r in self.records)
        
        return {
            "total_calls": total_calls,
            "total_spend_usd": self.total_spend_usd,
            "total_tokens": total_tokens,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_calls if total_calls > 0 else 0.0,
            "recent_calls": [r.to_dict() for r in self.records[-5:]]  # Last 5 calls
        }
