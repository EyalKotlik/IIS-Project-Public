"""
Live API tests that make actual calls to OpenAI.

These tests are SKIPPED by default to avoid costs.
To run them, set both:
  - OPENAI_API_KEY environment variable
  - RUN_LIVE_API_TESTS=1 environment variable

Example:
    RUN_LIVE_API_TESTS=1 pytest -m live_api -s
"""
