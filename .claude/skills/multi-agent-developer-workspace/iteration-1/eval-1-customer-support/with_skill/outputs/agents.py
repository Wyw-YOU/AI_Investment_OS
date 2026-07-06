"""
Specialized Agents
==================
Concrete agent implementations for the customer support workflow:

* ``ClassifierAgent`` -- classifies urgency + topic
* ``TechnicalAgent``   -- drafts technical support responses
* ``BillingAgent``     -- drafts billing support responses
* ``GeneralAgent``     -- drafts general-inquiry responses
* ``ResponseAgent``    -- polishes the specialist draft into a final response

Each agent:
  - inherits from ``BaseAgent``
  - uses the structured prompts from ``prompts.py``
  - returns a *partial state update* (immutability pattern)
  - catches its own errors and returns safe fallback values
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from base import AgentExecutionError, AgentOutput, BaseAgent
from prompts import (
    BILLING_SYSTEM_PROMPT,
    CLASSIFIER_SYSTEM_PROMPT,
    GENERAL_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    TECHNICAL_SYSTEM_PROMPT,
    build_billing_prompt,
    build_classifier_prompt,
    build_general_prompt,
    build_response_prompt,
    build_technical_prompt,
)

from state import (
    AgentResponse,
    ClassificationResult,
    FinalResponse,
    TicketStatus,
    Topic,
    Urgency,
)

logger = logging.getLogger(__name__)


# ===================================================================
# 1. CLASSIFIER AGENT
# ===================================================================

class ClassifierAgent(BaseAgent):
    """
    Analyses an incoming support ticket and classifies:
      - urgency: low / medium / high / critical
      - topic:   technical / billing / general / escalation

    Output goes into ``state["classification"]`` and drives routing.
    """

    name = "classifier_agent"
    description = (
        "Expert in triaging support tickets by urgency and topic."
    )

    # -- prompt construction -----------------------------------------------

    def build_prompt(self, state: dict[str, Any]) -> str:  # noqa: D102
        return build_classifier_prompt(state)

    def _get_system_prompt(self) -> str:
        return CLASSIFIER_SYSTEM_PROMPT

    # -- main execution ----------------------------------------------------

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Returns
        -------
        dict
            Partial state update with ``classification``, ``urgency``,
            ``topic``, and updated ``status``.
        """
        try:
            prompt = self.build_prompt(state)
            raw = self.call_llm(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.1,
                max_tokens=300,
            )
            parsed = self.parse_response(raw)

            # Validate and normalise
            urgency = parsed.get("urgency", Urgency.MEDIUM.value)
            topic = parsed.get("topic", Topic.GENERAL.value)

            if urgency not in [u.value for u in Urgency]:
                urgency = Urgency.MEDIUM.value
            if topic not in [t.value for t in Topic]:
                topic = Topic.GENERAL.value

            classification = ClassificationResult(
                urgency=urgency,
                topic=topic,
                reasoning=parsed.get("reasoning", ""),
                confidence=float(parsed.get("confidence", 0.5)),
            )

            return {
                "classification": classification,
                "urgency": urgency,
                "topic": topic,
                "status": TicketStatus.ROUTING.value,
            }

        except NotImplementedError:
            # No LLM wired -- return deterministic stub for demo/testing
            return self._stub_classification(state)

        except Exception as exc:
            logger.error("ClassifierAgent failed: %s", exc, exc_info=True)
            return {
                "classification": ClassificationResult(
                    urgency=Urgency.MEDIUM.value,
                    topic=Topic.GENERAL.value,
                    reasoning=f"Classification failed: {exc}",
                    confidence=0.0,
                ),
                "urgency": Urgency.MEDIUM.value,
                "topic": Topic.GENERAL.value,
                "status": TicketStatus.CLASSIFYING.value,
                "errors": [f"ClassifierAgent: {exc}"],
            }

    # -- deterministic stub for offline usage -------------------------------

    @staticmethod
    def _stub_classification(state: dict[str, Any]) -> dict[str, Any]:
        """Rule-based heuristic when no LLM is available."""
        msg = (state.get("customer_message", "") + " " + state.get("subject", "")).lower()

        # Urgency heuristics
        if any(w in msg for w in ["down", "outage", "critical", "emergency", "breach"]):
            urgency = Urgency.CRITICAL.value
        elif any(w in msg for w in ["urgent", "asap", "immediately", "broken"]):
            urgency = Urgency.HIGH.value
        elif any(w in msg for w in ["issue", "problem", "error", "bug"]):
            urgency = Urgency.MEDIUM.value
        else:
            urgency = Urgency.LOW.value

        # Topic heuristics
        if any(w in msg for w in ["api", "error", "bug", "crash", "500", "timeout", "login"]):
            topic = Topic.TECHNICAL.value
        elif any(w in msg for w in ["charge", "invoice", "refund", "bill", "subscription", "payment"]):
            topic = Topic.BILLING.value
        elif any(w in msg for w in ["legal", "compliance", "lawyer", "sue"]):
            topic = Topic.ESCALATION.value
        else:
            topic = Topic.GENERAL.value

        classification = ClassificationResult(
            urgency=urgency,
            topic=topic,
            reasoning="Heuristic classification (no LLM available).",
            confidence=0.65,
        )
        return {
            "classification": classification,
            "urgency": urgency,
            "topic": topic,
            "status": TicketStatus.ROUTING.value,
        }


# ===================================================================
# 2. TECHNICAL SUPPORT AGENT
# ===================================================================

class TechnicalAgent(BaseAgent):
    """
    Drafts a technical support response for tickets classified as
    ``topic == "technical"``.
    """

    name = "technical_agent"
    description = (
        "Senior Technical Support Engineer specialising in software "
        "troubleshooting, API integrations, and debugging."
    )

    def build_prompt(self, state: dict[str, Any]) -> str:
        return build_technical_prompt(state)

    def _get_system_prompt(self) -> str:
        return TECHNICAL_SYSTEM_PROMPT

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Return partial state update with ``agent_outputs`` entry."""
        try:
            prompt = self.build_prompt(state)
            raw = self.call_llm(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.3,
                max_tokens=1500,
            )
            parsed = self.parse_response(raw)

            response: AgentResponse = {
                "agent_name": self.name,
                "response_text": parsed.get("response_text", ""),
                "actions_taken": parsed.get("actions_taken", []),
                "follow_up_questions": parsed.get("follow_up_questions", []),
                "confidence": float(parsed.get("confidence", 0.5)),
                "citations": parsed.get("citations", []),
            }
            return {
                "agent_outputs": [response],
                "status": TicketStatus.AWAITING_RESPONSE.value,
            }

        except NotImplementedError:
            return self._stub_response(state)

        except Exception as exc:
            logger.error("TechnicalAgent failed: %s", exc, exc_info=True)
            return self._fallback(state, exc)

    @staticmethod
    def _stub_response(state: dict[str, Any]) -> dict[str, Any]:
        msg = state.get("customer_message", "")
        response: AgentResponse = {
            "agent_name": "technical_agent",
            "response_text": (
                f"Thank you for reaching out. I understand you're experiencing "
                f"a technical issue. I'd like to help you resolve this as "
                f"quickly as possible.\n\n"
                f"Could you please provide:\n"
                f"1. The exact error message you're seeing\n"
                f"2. Steps to reproduce the issue\n"
                f"3. Your environment details (OS, browser, API version)\n\n"
                f"In the meantime, please try clearing your cache and "
                f"checking our status page at status.example.com."
            ),
            "actions_taken": [
                "Requested reproduction steps",
                "Suggested cache clearing",
                "Referred to status page",
            ],
            "follow_up_questions": [
                "Can you share the exact error message or screenshot?",
                "When did this issue first occur?",
            ],
            "confidence": 0.6,
            "citations": ["https://docs.example.com/troubleshooting"],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.AWAITING_RESPONSE.value,
        }

    @staticmethod
    def _fallback(state: dict[str, Any], exc: Exception) -> dict[str, Any]:
        response: AgentResponse = {
            "agent_name": "technical_agent",
            "response_text": (
                "Thank you for contacting technical support. "
                "We are reviewing your issue and will get back to you shortly."
            ),
            "actions_taken": ["Escalated to engineering team"],
            "follow_up_questions": [],
            "confidence": 0.2,
            "citations": [],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.IN_PROGRESS.value,
            "errors": [f"TechnicalAgent: {exc}"],
        }


# ===================================================================
# 3. BILLING SUPPORT AGENT
# ===================================================================

class BillingAgent(BaseAgent):
    """
    Drafts a billing / invoicing support response for tickets classified
    as ``topic == "billing"``.
    """

    name = "billing_agent"
    description = (
        "Billing Support Specialist expert in invoicing, refunds, "
        "subscription management, and payment processing."
    )

    def build_prompt(self, state: dict[str, Any]) -> str:
        return build_billing_prompt(state)

    def _get_system_prompt(self) -> str:
        return BILLING_SYSTEM_PROMPT

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            prompt = self.build_prompt(state)
            raw = self.call_llm(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.2,
                max_tokens=1500,
            )
            parsed = self.parse_response(raw)

            response: AgentResponse = {
                "agent_name": self.name,
                "response_text": parsed.get("response_text", ""),
                "actions_taken": parsed.get("actions_taken", []),
                "follow_up_questions": parsed.get("follow_up_questions", []),
                "confidence": float(parsed.get("confidence", 0.5)),
                "citations": parsed.get("citations", []),
            }
            return {
                "agent_outputs": [response],
                "status": TicketStatus.AWAITING_RESPONSE.value,
            }

        except NotImplementedError:
            return self._stub_response(state)

        except Exception as exc:
            logger.error("BillingAgent failed: %s", exc, exc_info=True)
            return self._fallback(state, exc)

    @staticmethod
    def _stub_response(state: dict[str, Any]) -> dict[str, Any]:
        response: AgentResponse = {
            "agent_name": "billing_agent",
            "response_text": (
                "Thank you for contacting our billing team. "
                "I'm sorry for any inconvenience with your account.\n\n"
                "I'm currently reviewing your billing history to "
                "investigate the issue. To help me resolve this faster, "
                "could you please confirm:\n"
                "1. Your account email or customer ID\n"
                "2. The date and amount of the disputed charge\n"
                "3. Your preferred resolution (refund, credit, etc.)\n\n"
                "I'll prioritise this and follow up within 24 hours."
            ),
            "actions_taken": [
                "Initiated billing history review",
                "Requested account identification",
            ],
            "follow_up_questions": [
                "Can you confirm your account email or customer ID?",
                "What is the date and amount of the disputed charge?",
            ],
            "confidence": 0.6,
            "citations": ["https://billing.example.com/refund-policy"],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.AWAITING_RESPONSE.value,
        }

    @staticmethod
    def _fallback(state: dict[str, Any], exc: Exception) -> dict[str, Any]:
        response: AgentResponse = {
            "agent_name": "billing_agent",
            "response_text": (
                "Thank you for contacting billing support. "
                "We are looking into your account and will respond shortly."
            ),
            "actions_taken": ["Flagged for manual review"],
            "follow_up_questions": [],
            "confidence": 0.2,
            "citations": [],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.IN_PROGRESS.value,
            "errors": [f"BillingAgent: {exc}"],
        }


# ===================================================================
# 4. GENERAL INQUIRIES AGENT
# ===================================================================

class GeneralAgent(BaseAgent):
    """
    Handles non-technical, non-billing questions such as product
    information, how-to guidance, and feature requests.
    """

    name = "general_agent"
    description = (
        "Customer Success Representative handling product questions, "
        "feature requests, and general guidance."
    )

    def build_prompt(self, state: dict[str, Any]) -> str:
        return build_general_prompt(state)

    def _get_system_prompt(self) -> str:
        return GENERAL_SYSTEM_PROMPT

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            prompt = self.build_prompt(state)
            raw = self.call_llm(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.5,
                max_tokens=1500,
            )
            parsed = self.parse_response(raw)

            response: AgentResponse = {
                "agent_name": self.name,
                "response_text": parsed.get("response_text", ""),
                "actions_taken": parsed.get("actions_taken", []),
                "follow_up_questions": parsed.get("follow_up_questions", []),
                "confidence": float(parsed.get("confidence", 0.5)),
                "citations": parsed.get("citations", []),
            }
            return {
                "agent_outputs": [response],
                "status": TicketStatus.AWAITING_RESPONSE.value,
            }

        except NotImplementedError:
            return self._stub_response(state)

        except Exception as exc:
            logger.error("GeneralAgent failed: %s", exc, exc_info=True)
            return self._fallback(state, exc)

    @staticmethod
    def _stub_response(state: dict[str, Any]) -> dict[str, Any]:
        response: AgentResponse = {
            "agent_name": "general_agent",
            "response_text": (
                f"Hi {state.get('customer_name', 'there')}! "
                f"Thanks for reaching out to us.\n\n"
                f"I'd be happy to help with your question. "
                f"Here are some resources that might be useful:\n"
                f"- Help Center: https://help.example.com\n"
                f"- Community Forum: https://community.example.com\n"
                f"- Video Tutorials: https://tutorials.example.com\n\n"
                f"Please let me know if you need anything else!"
            ),
            "actions_taken": [
                "Provided help center links",
                "Offered additional assistance",
            ],
            "follow_up_questions": [
                "Is there anything specific I can help you with?",
            ],
            "confidence": 0.7,
            "citations": ["https://help.example.com"],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.AWAITING_RESPONSE.value,
        }

    @staticmethod
    def _fallback(state: dict[str, Any], exc: Exception) -> dict[str, Any]:
        response: AgentResponse = {
            "agent_name": "general_agent",
            "response_text": (
                "Thank you for contacting us! "
                "A team member will review your question and respond shortly."
            ),
            "actions_taken": ["Queued for human review"],
            "follow_up_questions": [],
            "confidence": 0.2,
            "citations": [],
        }
        return {
            "agent_outputs": [response],
            "status": TicketStatus.IN_PROGRESS.value,
            "errors": [f"GeneralAgent: {exc}"],
        }


# ===================================================================
# 5. RESPONSE POLISH / SYNTHESIS AGENT
# ===================================================================

class ResponseAgent(BaseAgent):
    """
    Takes the specialist agent's draft and produces a polished,
    customer-ready final response with internal notes.
    """

    name = "response_agent"
    description = (
        "Response Quality Agent that polishes drafts into customer-ready "
        "replies with consistent tone and completeness."
    )

    def build_prompt(
        self,
        state: dict[str, Any],
        agent_output: dict[str, Any] | None = None,
    ) -> str:
        if agent_output is None:
            # Grab the first (and in our flow, only) specialist output
            outputs = state.get("agent_outputs", [])
            agent_output = outputs[0] if outputs else {}
        return build_response_prompt(state, agent_output)

    def _get_system_prompt(self) -> str:
        return RESPONSE_SYSTEM_PROMPT

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            outputs = state.get("agent_outputs", [])
            if not outputs:
                return self._no_draft_fallback(state)

            agent_output = outputs[0]  # the routed specialist

            prompt = self.build_prompt(state, agent_output)
            raw = self.call_llm(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.4,
                max_tokens=2000,
            )
            parsed = self.parse_response(raw)

            final_response = FinalResponse(
                subject=parsed.get(
                    "subject",
                    f"Re: {state.get('subject', 'Your Support Request')}",
                ),
                body=parsed.get("body", agent_output.get("response_text", "")),
                tone=parsed.get("tone", "professional"),
                internal_notes=parsed.get("internal_notes", ""),
                next_steps=parsed.get("next_steps", []),
            )

            return {
                "final_response": final_response,
                "status": TicketStatus.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat(),
            }

        except NotImplementedError:
            return self._stub_finalise(state)

        except Exception as exc:
            logger.error("ResponseAgent failed: %s", exc, exc_info=True)
            return self._fallback(state, exc)

    # -- stubs --------------------------------------------------------------

    @staticmethod
    def _stub_finalise(state: dict[str, Any]) -> dict[str, Any]:
        outputs = state.get("agent_outputs", [])
        draft = outputs[0] if outputs else {}
        customer_name = state.get("customer_name", "there")
        draft_body = draft.get("response_text", "We are reviewing your request.")

        final_response = FinalResponse(
            subject=f"Re: {state.get('subject', 'Your Support Request')}",
            body=f"Hi {customer_name},\n\n{draft_body}\n\nBest regards,\nSupport Team",
            tone="professional",
            internal_notes=(
                f"Ticket routed to {draft.get('agent_name', 'N/A')}. "
                f"Draft confidence: {draft.get('confidence', 'N/A')}."
            ),
            next_steps=["Monitor for customer reply", "Follow up in 48h if no response"],
        )
        return {
            "final_response": final_response,
            "status": TicketStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _no_draft_fallback(state: dict[str, Any]) -> dict[str, Any]:
        final_response = FinalResponse(
            subject=f"Re: {state.get('subject', 'Your Support Request')}",
            body=(
                "Thank you for contacting us. "
                "A support representative will review your request and "
                "get back to you as soon as possible."
            ),
            tone="professional",
            internal_notes="No specialist draft available; sent generic acknowledgement.",
            next_steps=["Assign to human agent"],
        )
        return {
            "final_response": final_response,
            "status": TicketStatus.ESCALATED.value,
            "errors": ["ResponseAgent: no specialist draft found"],
        }

    @staticmethod
    def _fallback(state: dict[str, Any], exc: Exception) -> dict[str, Any]:
        outputs = state.get("agent_outputs", [])
        draft = outputs[0] if outputs else {}
        final_response = FinalResponse(
            subject=f"Re: {state.get('subject', 'Your Support Request')}",
            body=draft.get(
                "response_text",
                "We are reviewing your request and will respond shortly.",
            ),
            tone="professional",
            internal_notes=f"ResponseAgent failed: {exc}. Used raw draft.",
            next_steps=["Human review required"],
        )
        return {
            "final_response": final_response,
            "status": TicketStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "errors": [f"ResponseAgent: {exc}"],
        }
