#!/usr/bin/env python3
"""
LLM Integration Demo Script
============================

This script demonstrates the LLM integration with caching and budget tracking.
It will only make real API calls if OPENAI_API_KEY is set.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.llm_client import get_llm_client, reset_llm_client
from app_mockup.backend.llm_schemas import ComponentClassificationResult
from app_mockup.backend.llm_exceptions import LLMAPIKeyMissingError


def main():
    """Run the demo."""
    print("="*70)
    print("LLM Integration Demo")
    print("="*70)
    print()
    
    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print()
        print("To use the LLM integration, you need to set your OpenAI API key:")
        print()
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print()
        print("Or create a .streamlit/secrets.toml file:")
        print()
        print('  OPENAI_API_KEY = "your-api-key-here"')
        print()
        print("The integration is fully functional and ready to use once the key is set.")
        print()
        print("Features:")
        print("  ✓ Structured outputs (Pydantic schemas)")
        print("  ✓ Persistent caching (SQLite in .cache/)")
        print("  ✓ Budget tracking with hard caps")
        print("  ✓ Automatic retry and error handling")
        print("  ✓ Token usage tracking and cost estimation")
        print()
        return 1
    
    print("✓ OPENAI_API_KEY is configured")
    print()
    
    try:
        # Get the LLM client
        client = get_llm_client()
        print(f"✓ LLM Client initialized")
        print(f"  Model: {client.config.model}")
        print(f"  Temperature: {client.config.temperature}")
        print(f"  Cache enabled: {client.config.cache_enabled}")
        print(f"  Budget: ${client.config.budget_usd:.2f}")
        print()
        
        # Get initial stats
        stats = client.get_stats()
        print("Current Usage:")
        print(f"  Total spend: ${stats['budget']['total_spend_usd']:.6f}")
        print(f"  Total calls: {stats['budget']['total_calls']}")
        print(f"  Cache entries: {stats['cache']['total_entries']}")
        print()
        
        # Example prompt
        example_text = "Electric cars are the future because they reduce pollution."
        
        print("Example Classification Task:")
        print(f"  Text: \"{example_text}\"")
        print()
        print("Making LLM call... (this may take a few seconds)")
        
        # Make the LLM call
        result = client.call_llm(
            task_name="demo_classification",
            system_prompt="You are an argument mining expert. Classify the given text as 'claim', 'premise', 'objection', 'reply', or 'other'.",
            user_prompt=f"Classify this text: \"{example_text}\"\n\nProvide the classification type, confidence score (0-1), and a brief rationale.",
            schema=ComponentClassificationResult
        )
        
        classification = result["result"]
        usage = result["usage"]
        
        print()
        print("✓ Classification successful!")
        print(f"  Label: {classification.label}")
        print(f"  Confidence: {classification.confidence:.2f}")
        if classification.rationale_short:
            print(f"  Rationale: {classification.rationale_short}")
        print()
        print("Usage:")
        print(f"  Input tokens: {usage['input_tokens']}")
        print(f"  Output tokens: {usage['output_tokens']}")
        print(f"  Cost: ${usage['estimated_cost_usd']:.6f}")
        print(f"  Cache hit: {result['cache_hit']}")
        print()
        
        # Try calling again to demonstrate caching
        print("Calling again with same input to demonstrate caching...")
        result2 = client.call_llm(
            task_name="demo_classification",
            system_prompt="You are an argument mining expert. Classify the given text as 'claim', 'premise', 'objection', 'reply', or 'other'.",
            user_prompt=f"Classify this text: \"{example_text}\"\n\nProvide the classification type, confidence score (0-1), and a brief rationale.",
            schema=ComponentClassificationResult
        )
        
        print()
        print("✓ Second call completed!")
        print(f"  Cache hit: {result2['cache_hit']}")
        print(f"  Cost: ${result2['usage']['estimated_cost_usd']:.6f} (cache hits are free!)")
        print()
        
        # Final stats
        final_stats = client.get_stats()
        print("Final Usage:")
        print(f"  Total spend: ${final_stats['budget']['total_spend_usd']:.6f}")
        print(f"  Total calls: {final_stats['budget']['total_calls']}")
        print(f"  Cache hit rate: {final_stats['budget']['cache_hit_rate']*100:.1f}%")
        print()
        
        print("="*70)
        print("Demo completed successfully!")
        print("="*70)
        return 0
        
    except LLMAPIKeyMissingError:
        print("❌ Error: API key validation failed")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
