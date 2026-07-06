"""
Multi-Agent Customer Support System.

A complete implementation of a multi-agent customer support workflow
using LangGraph for orchestration, with structured prompts, output
parsing, state management, and error handling.

Modules:
    state          - TypedDict state schema and dataclasses
    agents         - Agent definitions (Classifier, Technical, Billing, General, Response)
    prompts        - Structured prompt templates for each agent
    parsers        - JSON extraction and output validation
    error_handling - Retry, circuit breaker, and safe node wrappers
    state_manager  - Ticket store, lifecycle tracker, metrics
    workflow       - LangGraph StateGraph assembly
    main           - Entry point and demo runner
"""

__version__ = "1.0.0"
