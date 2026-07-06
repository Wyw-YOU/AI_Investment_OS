"""
Agent Definitions for the Multi-Agent Customer Support System.

Each agent is a self-contained unit that:
  1. Reads its relevant fields from the shared SupportTicketState.
  2. Calls the LLM via the agent-specific prompt.
  3. Parses and validates the LLM output.
  4. Writes its result back to the appropriate state field.
  5. Records an AgentDecision for the audit trail.

Agents:
  - ClassifierAgent   : determines urgency + topic + sentiment
  - TechnicalAgent    : handles technical support tickets
  - BillingAgent      : handles billing / payment tickets
  - GeneralAgent      : handles general inquiries
  - ResponseAgent     : polishes the specialist response for the customer
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from state import (
    AgentDecision,
    AgentResponse,
    ClassificationResult,
    FinalResponse,
    SupportTicketState,
    TicketStatus,
    UrgencyLevel,
    TopicCategory,
)
from prompts import (
    build_classifier_prompt,
    build_technical_prompt,
    build_billing_prompt,
    build_general_prompt,
    build_response_aggregator_prompt,
)
from parsers import (
    parse_classification,
    parse_agent_response,
    parse_final_response,
    ValidationError,
)
from error_handling import (
    LLMCallError,
    record_agent_decision,
    record_error,
    retry_with_backoff,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class BaseAgent(ABC):
    """
    Abstract base for all agents in the system.

    Subclasses implement:
      - `name`        : human-readable identifier
      - `_build_prompt`: construct the LLM message list
      - `_process`     : parse the LLM response and update state
    """

    name: str = "base_agent"

    def __init__(self, llm_client: Any = None) -> None:
        """
        Parameters
        ----------
        llm_client : Any
            An object with a `.chat(messages, temperature, max_tokens)` method.
            The method must return an object with a `.content` attribute
            containing the raw LLM text.

            In production this is typically an OpenAI-compatible client.
            For testing, pass a MockLLMClient (see tests/).
        """
        self._llm = llm_client

    # -- Public interface ----------------------------------------------------

    def __call__(self, state: SupportTicketState) -> SupportTicketState:
        """
        LangGraph node entry point.

        Updates the state in-place and returns it.
        """
        logger.info("[%s] Processing ticket %s", self.name, state["ticket"]["ticket_id"])

        # 1. Build prompt
        messages = self._build_prompt(state)

        # 2. Call LLM
        raw_response = self._call_llm(messages)

        # 3. Parse and write results back to state
        state = self._process(state, raw_response)

        logger.info("[%s] Done processing ticket %s", self.name, state["ticket"]["ticket_id"])
        return state

    # -- Internal hooks (subclass must implement) ----------------------------

    @abstractmethod
    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ...

    @abstractmethod
    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        ...

    # -- LLM invocation (with retry) -----------------------------------------

    @retry_with_backoff(max_retries=2, base_delay=1.0)
    def _call_llm(self, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        """
        Call the LLM and return the raw text response.

        Uses retry_with_backoff for transient failures.  Raises LLMCallError
        if no LLM client is configured.
        """
        if self._llm is None:
            # Deterministic fallback for demo / testing without a live LLM
            return self._deterministic_fallback(messages)

        try:
            response = self._llm.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
            )
            return response.content
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", self.name, exc)
            raise LLMCallError(f"{self.name} LLM call failed: {exc}") from exc

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        """
        Return a hard-coded JSON response when no LLM client is provided.

        This enables the system to run end-to-end in tests and demos.
        Subclasses should override this with appropriate fallback logic.
        """
        raise LLMCallError(
            f"No LLM client configured for {self.name} and no "
            "deterministic fallback implemented."
        )


# ---------------------------------------------------------------------------
# Classifier Agent
# ---------------------------------------------------------------------------


class ClassifierAgent(BaseAgent):
    """
    Analyzes an incoming ticket and produces a ClassificationResult
    containing urgency, topic, sentiment, and keywords.
    """

    name = "classifier_agent"

    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ticket = state["ticket"]
        return build_classifier_prompt(ticket)

    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        try:
            parsed = parse_classification(raw_response)
            classification = parsed.to_result()

            state["classification"] = classification
            state["urgency_level"] = classification["urgency"]
            state["assigned_topic"] = classification["topic"]
            state["ticket_status"] = TicketStatus.CLASSIFYING.value

            record_agent_decision(
                state,
                agent_name=self.name,
                decision=f"urgency={classification['urgency']}, topic={classification['topic']}",
                confidence=classification["confidence"],
                reasoning=classification["reasoning"],
            )
        except (ValidationError, KeyError) as exc:
            logger.error("[%s] Parsing failed: %s", self.name, exc)
            record_error(state, f"[{self.name}] Parse error: {exc}")
            # Apply safe defaults
            state.setdefault("classification", {})
            state["urgency_level"] = UrgencyLevel.MEDIUM.value
            state["assigned_topic"] = TopicCategory.GENERAL.value
            state["ticket_status"] = TicketStatus.ERROR.value

        return state

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        """Provide a sensible default classification for demo purposes."""
        # Extract subject from the user message for keyword-based classification
        user_msg = messages[-1]["content"] if messages else ""
        subject_lower = user_msg.lower()

        urgency = UrgencyLevel.MEDIUM.value
        topic = TopicCategory.GENERAL.value
        sentiment = "neutral"
        keywords: list[str] = []

        # Simple keyword heuristics
        if any(w in subject_lower for w in ["outage", "down", "critical", "security", "breach"]):
            urgency = UrgencyLevel.CRITICAL.value
        elif any(w in subject_lower for w in ["error", "broken", "fail", "bug"]):
            urgency = UrgencyLevel.HIGH.value
        elif any(w in subject_lower for w in ["question", "how to", "help"]):
            urgency = UrgencyLevel.LOW.value

        if any(w in subject_lower for w in ["api", "error", "bug", "crash", "timeout", "login", "technical"]):
            topic = TopicCategory.TECHNICAL.value
            keywords = ["api", "error", "technical"]
        elif any(w in subject_lower for w in ["billing", "charge", "payment", "invoice", "refund", "subscription"]):
            topic = TopicCategory.BILLING.value
            keywords = ["billing", "payment"]
        else:
            topic = TopicCategory.GENERAL.value
            keywords = ["general", "inquiry"]

        if any(w in subject_lower for w in ["angry", "frustrated", "terrible", "worst"]):
            sentiment = "negative"
        elif any(w in subject_lower for w in ["great", "love", "excellent", "thank"]):
            sentiment = "positive"

        result = {
            "urgency": urgency,
            "topic": topic,
            "sentiment": sentiment,
            "keywords": keywords,
            "confidence": 0.75,
            "reasoning": f"Classified by keyword heuristics (no LLM). Subject analysis: '{subject_lower[:100]}'",
        }
        return json.dumps(result)


# ---------------------------------------------------------------------------
# Technical Support Agent
# ---------------------------------------------------------------------------


class TechnicalAgent(BaseAgent):
    """
    Handles technical support tickets: troubleshooting, bug reports,
    API issues, and system diagnostics.
    """

    name = "technical_agent"

    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ticket = state["ticket"]
        urgency = state.get("urgency_level", "medium")
        return build_technical_prompt(ticket, urgency)

    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        try:
            parsed = parse_agent_response(raw_response, expected_agent="technical_agent")
            response = parsed.to_response()

            state["technical_response"] = response
            state["active_response"] = response
            state["ticket_status"] = TicketStatus.PROCESSING.value

            record_agent_decision(
                state,
                agent_name=self.name,
                decision="technical_analysis_complete",
                confidence=response["confidence"],
                reasoning=response.get("internal_notes", ""),
            )
        except (ValidationError, KeyError) as exc:
            logger.error("[%s] Parsing failed: %s", self.name, exc)
            record_error(state, f"[{self.name}] Parse error: {exc}")
            state["ticket_status"] = TicketStatus.ERROR.value

        return state

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        user_msg = messages[-1]["content"] if messages else ""
        response = {
            "agent_name": "technical_agent",
            "response_text": (
                "Thank you for reporting this technical issue. Based on the information provided, "
                "I recommend the following troubleshooting steps:\n\n"
                "1. Clear your browser cache and cookies.\n"
                "2. Try accessing the service from an incognito/private window.\n"
                "3. Check our status page at status.example.com for any known outages.\n"
                "4. If the issue persists, please provide the following information:\n"
                "   - Browser and version\n"
                "   - Operating system\n"
                "   - Screenshots of any error messages\n"
                "   - Steps to reproduce the issue\n\n"
                "Our technical team will investigate further once we have these details."
            ),
            "follow_up_actions": [
                "Gather diagnostic information from customer",
                "Check error logs for related issues",
                "Verify service health on status page",
            ],
            "requires_escalation": False,
            "escalation_reason": "",
            "internal_notes": "Standard troubleshooting steps provided. Awaiting customer response with diagnostics.",
            "confidence": 0.70,
        }
        return json.dumps(response)


# ---------------------------------------------------------------------------
# Billing Support Agent
# ---------------------------------------------------------------------------


class BillingAgent(BaseAgent):
    """
    Handles billing and payment-related tickets: charges, refunds,
    subscriptions, and invoicing.
    """

    name = "billing_agent"

    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ticket = state["ticket"]
        urgency = state.get("urgency_level", "medium")
        return build_billing_prompt(ticket, urgency)

    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        try:
            parsed = parse_agent_response(raw_response, expected_agent="billing_agent")
            response = parsed.to_response()

            state["billing_response"] = response
            state["active_response"] = response
            state["ticket_status"] = TicketStatus.PROCESSING.value

            record_agent_decision(
                state,
                agent_name=self.name,
                decision="billing_analysis_complete",
                confidence=response["confidence"],
                reasoning=response.get("internal_notes", ""),
            )
        except (ValidationError, KeyError) as exc:
            logger.error("[%s] Parsing failed: %s", self.name, exc)
            record_error(state, f"[{self.name}] Parse error: {exc}")
            state["ticket_status"] = TicketStatus.ERROR.value

        return state

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        response = {
            "agent_name": "billing_agent",
            "response_text": (
                "Thank you for reaching out about your billing concern. "
                "I've reviewed your account and here's what I can share:\n\n"
                "1. Your most recent billing statement was generated on the 1st of this month.\n"
                "2. If you see an unexpected charge, it may be related to a plan upgrade "
                "or add-on service.\n"
                "3. For a detailed breakdown of charges, please visit your account's "
                "Billing History page.\n\n"
                "If you believe there is an error, I can initiate a review. "
                "Please confirm the specific charge amount and date so I can investigate further."
            ),
            "follow_up_actions": [
                "Review customer billing history",
                "Verify charge details against subscription plan",
                "Initiate refund review if charge is erroneous",
            ],
            "requires_escalation": False,
            "escalation_reason": "",
            "internal_notes": "Standard billing inquiry. No anomalies detected in account overview.",
            "confidence": 0.75,
        }
        return json.dumps(response)


# ---------------------------------------------------------------------------
# General Inquiry Agent
# ---------------------------------------------------------------------------


class GeneralAgent(BaseAgent):
    """
    Handles general inquiries: product questions, feature requests,
    account issues, and anything not clearly technical or billing.
    """

    name = "general_agent"

    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ticket = state["ticket"]
        urgency = state.get("urgency_level", "medium")
        return build_general_prompt(ticket, urgency)

    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        try:
            parsed = parse_agent_response(raw_response, expected_agent="general_agent")
            response = parsed.to_response()

            state["general_response"] = response
            state["active_response"] = response
            state["ticket_status"] = TicketStatus.PROCESSING.value

            record_agent_decision(
                state,
                agent_name=self.name,
                decision="general_analysis_complete",
                confidence=response["confidence"],
                reasoning=response.get("internal_notes", ""),
            )
        except (ValidationError, KeyError) as exc:
            logger.error("[%s] Parsing failed: %s", self.name, exc)
            record_error(state, f"[{self.name}] Parse error: {exc}")
            state["ticket_status"] = TicketStatus.ERROR.value

        return state

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        response = {
            "agent_name": "general_agent",
            "response_text": (
                "Thank you for contacting us! I'd be happy to help with your inquiry.\n\n"
                "Based on your message, here's what I can share:\n\n"
                "1. For frequently asked questions, please visit our Help Center at "
                "help.example.com.\n"
                "2. If you need to update your account information, you can do so from "
                "the Settings page.\n"
                "3. For feature requests, we appreciate your feedback! I've logged your "
                "suggestion for our product team to review.\n\n"
                "Is there anything else I can help you with? I'm here to ensure you have "
                "the best experience with our service."
            ),
            "follow_up_actions": [
                "Log feature request in product backlog",
                "Send link to Help Center",
                "Follow up in 48 hours if no response",
            ],
            "requires_escalation": False,
            "escalation_reason": "",
            "internal_notes": "General inquiry handled. Customer may benefit from self-service resources.",
            "confidence": 0.80,
        }
        return json.dumps(response)


# ---------------------------------------------------------------------------
# Response Aggregator Agent
# ---------------------------------------------------------------------------


class ResponseAgent(BaseAgent):
    """
    Reviews the specialist agent's response and produces a polished,
    customer-facing final response.

    This agent acts as the quality gate before any message reaches the
    customer.
    """

    name = "response_agent"

    def _build_prompt(self, state: SupportTicketState) -> list[dict[str, str]]:
        ticket = state["ticket"]
        urgency = state.get("urgency_level", "medium")
        topic = state.get("assigned_topic", "general")
        active = state.get("active_response", {})
        return build_response_aggregator_prompt(ticket, urgency, topic, active)

    def _process(
        self, state: SupportTicketState, raw_response: str
    ) -> SupportTicketState:
        try:
            parsed = parse_final_response(raw_response)
            final = parsed.to_final()

            state["final_response"] = final
            state["ticket_status"] = TicketStatus.COMPLETED.value

            record_agent_decision(
                state,
                agent_name=self.name,
                decision=f"final_response_generated, status={final['resolution_status']}",
                confidence=0.0,  # aggregator does not output its own confidence
                reasoning=final["ticket_summary"],
            )
        except (ValidationError, KeyError) as exc:
            logger.error("[%s] Parsing failed: %s", self.name, exc)
            record_error(state, f"[{self.name}] Parse error: {exc}")
            # Still produce a fallback response so the ticket is not stuck
            active = state.get("active_response", {})
            state["final_response"] = FinalResponse(
                customer_facing_message=active.get("response_text", "We are looking into your request."),
                ticket_summary="Fallback response generated due to aggregator error.",
                resolution_status="pending",
                follow_up_required=True,
                estimated_resolution_time="24 hours",
                reference_number=state["ticket"]["ticket_id"],
            )
            state["ticket_status"] = TicketStatus.COMPLETED.value

        return state

    def _deterministic_fallback(self, messages: list[dict[str, str]]) -> str:
        # Extract the specialist response from the user message
        user_msg = messages[-1]["content"] if messages else ""

        # Try to find the ticket ID in the message
        ticket_id = "UNKNOWN"
        for line in user_msg.split("\n"):
            if "Ticket ID:" in line:
                ticket_id = line.split("Ticket ID:")[-1].strip()
                break

        # Try to find the specialist response
        response_text = ""
        for line in user_msg.split("\n"):
            if "Response:" in line:
                response_text = line.split("Response:")[-1].strip()
                break

        if not response_text:
            response_text = "We are currently reviewing your request and will provide a detailed response shortly."

        final = {
            "customer_facing_message": (
                f"Dear Customer,\n\n"
                f"Thank you for contacting our support team. "
                f"{response_text}\n\n"
                f"If you have any further questions, please don't hesitate to reach out. "
                f"We're here to help!\n\n"
                f"Best regards,\nCustomer Support Team"
            ),
            "ticket_summary": f"Support request {ticket_id} handled with standard response.",
            "resolution_status": "pending",
            "follow_up_required": True,
            "estimated_resolution_time": "24 hours",
            "reference_number": ticket_id,
        }
        return json.dumps(final)
