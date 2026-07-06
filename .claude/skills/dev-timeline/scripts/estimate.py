#!/usr/bin/env python3
"""
Development Timeline Estimation Tool for AI Investment OS

This script helps estimate development effort for various components
of the AI Investment OS project.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import json


class Complexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ComponentType(Enum):
    AGENT = "agent"
    SERVICE = "service"
    UI_COMPONENT = "ui_component"
    DATABASE = "database"
    API = "api"
    WORKFLOW = "workflow"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class EstimateResult:
    component_name: str
    component_type: ComponentType
    complexity: Complexity
    base_days: float
    buffer_days: float
    total_days: float
    tasks: List[str]
    dependencies: List[str]
    risks: List[str]


# Complexity multipliers
COMPLEXITY_MULTIPLIERS = {
    Complexity.LOW: 1.0,
    Complexity.MEDIUM: 1.5,
    Complexity.HIGH: 2.5,
    Complexity.VERY_HIGH: 4.0,
}

# Base estimates by component type (in days)
BASE_ESTIMATES = {
    ComponentType.AGENT: 5.0,
    ComponentType.SERVICE: 3.0,
    ComponentType.UI_COMPONENT: 2.0,
    ComponentType.DATABASE: 2.0,
    ComponentType.API: 2.5,
    ComponentType.WORKFLOW: 4.0,
    ComponentType.INFRASTRUCTURE: 3.0,
}

# Component-specific task templates
TASK_TEMPLATES = {
    "agent": [
        "Define agent interface and state",
        "Implement core logic",
        "Design prompts",
        "Add error handling",
        "Write unit tests",
        "Integration testing"
    ],
    "service": [
        "Define data models",
        "Implement business logic",
        "Create API endpoints",
        "Add validation",
        "Write tests",
        "Documentation"
    ],
    "ui_component": [
        "Design component structure",
        "Implement UI",
        "Add state management",
        "Style and polish",
        "Test interactions",
        "Accessibility review"
    ],
    "database": [
        "Design schema",
        "Create migrations",
        "Add indexes",
        "Write queries",
        "Test performance",
        "Documentation"
    ],
    "api": [
        "Define endpoints",
        "Implement handlers",
        "Add authentication",
        "Input validation",
        "Error handling",
        "API documentation"
    ],
    "workflow": [
        "Define workflow DAG",
        "Implement nodes",
        "Add state management",
        "Error handling",
        "Testing with mock data",
        "Performance optimization"
    ],
    "infrastructure": [
        "Setup configuration",
        "Docker setup",
        "CI/CD pipeline",
        "Monitoring",
        "Documentation",
        "Testing"
    ]
}


def estimate_component(
    name: str,
    component_type: ComponentType,
    complexity: Complexity,
    additional_factors: Optional[dict] = None
) -> EstimateResult:
    """
    Estimate development effort for a component.

    Args:
        name: Component name
        component_type: Type of component
        complexity: Complexity level
        additional_factors: Optional dict with additional factors (e.g., external_apis, team_experience)

    Returns:
        EstimateResult with detailed breakdown
    """
    base_days = BASE_ESTIMATES[component_type]
    multiplier = COMPLEXITY_MULTIPLIERS[complexity]

    # Adjust for additional factors
    factor_adjustment = 1.0
    if additional_factors:
        if additional_factors.get("external_apis"):
            factor_adjustment += 0.3
        if additional_factors.get("team_experience") == "low":
            factor_adjustment += 0.5
        if additional_factors.get("real_time"):
            factor_adjustment += 0.4
        if additional_factors.get("security_critical"):
            factor_adjustment += 0.3

    estimated_days = base_days * multiplier * factor_adjustment
    buffer_days = estimated_days * 0.25  # 25% buffer
    total_days = estimated_days + buffer_days

    # Get tasks based on component type
    tasks = TASK_TEMPLATES.get(component_type.value, [])

    # Common dependencies
    dependencies = []
    if component_type == ComponentType.AGENT:
        dependencies = ["LLM provider setup", "Base Agent class"]
    elif component_type == ComponentType.SERVICE:
        dependencies = ["Database setup", "Authentication"]
    elif component_type == ComponentType.UI_COMPONENT:
        dependencies = ["API endpoints", "Design system"]

    # Common risks
    risks = []
    if complexity in [Complexity.HIGH, Complexity.VERY_HIGH]:
        risks.append("Complex integration requirements")
    if component_type == ComponentType.AGENT:
        risks.append("Prompt quality iteration")
    if component_type == ComponentType.WORKFLOW:
        risks.append("Multi-agent coordination complexity")

    return EstimateResult(
        component_name=name,
        component_type=component_type,
        complexity=complexity,
        base_days=round(estimated_days, 1),
        buffer_days=round(buffer_days, 1),
        total_days=round(total_days, 1),
        tasks=tasks,
        dependencies=dependencies,
        risks=risks
    )


def estimate_agent(agent_name: str, complexity: Complexity) -> EstimateResult:
    """
    Estimate development effort for an AI agent.

    Args:
        agent_name: Name of the agent (e.g., "News Agent", "Financial Agent")
        complexity: Complexity level

    Returns:
        EstimateResult with detailed breakdown
    """
    additional_factors = {
        "external_apis": True,
        "real_time": True
    }
    return estimate_component(
        name=agent_name,
        component_type=ComponentType.AGENT,
        complexity=complexity,
        additional_factors=additional_factors
    )


def estimate_phase(phase_name: str, components: List[dict]) -> dict:
    """
    Estimate total effort for a development phase.

    Args:
        phase_name: Name of the phase
        components: List of component dicts with name, type, complexity

    Returns:
        Dict with phase summary and component breakdowns
    """
    component_estimates = []
    total_days = 0

    for comp in components:
        estimate = estimate_component(
            name=comp["name"],
            component_type=ComponentType(comp["type"]),
            complexity=Complexity(comp["complexity"]),
            additional_factors=comp.get("factors")
        )
        component_estimates.append(estimate)
        total_days += estimate.total_days

    return {
        "phase_name": phase_name,
        "total_days": round(total_days, 1),
        "total_weeks": round(total_days / 5, 1),
        "components": [
            {
                "name": est.component_name,
                "type": est.component_type.value,
                "complexity": est.complexity.value,
                "days": est.total_days,
                "tasks": est.tasks
            }
            for est in component_estimates
        ]
    }


def format_estimate(result: EstimateResult) -> str:
    """Format an estimate result as a readable string."""
    lines = [
        f"## {result.component_name}",
        f"",
        f"**Type**: {result.component_type.value}",
        f"**Complexity**: {result.complexity.value}",
        f"",
        f"### Time Estimate",
        f"- Base effort: {result.base_days} days",
        f"- Buffer (25%): {result.buffer_days} days",
        f"- **Total: {result.total_days} days**",
        f"",
        f"### Tasks",
    ]

    for i, task in enumerate(result.tasks, 1):
        lines.append(f"{i}. {task}")

    if result.dependencies:
        lines.append("")
        lines.append("### Dependencies")
        for dep in result.dependencies:
            lines.append(f"- {dep}")

    if result.risks:
        lines.append("")
        lines.append("### Risks")
        for risk in result.risks:
            lines.append(f"- {risk}")

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Estimate News Agent
    news_agent = estimate_agent("News Agent", Complexity.HIGH)
    print(format_estimate(news_agent))
    print("\n" + "="*50 + "\n")

    # Estimate a full phase
    phase_components = [
        {"name": "Stock Service", "type": "service", "complexity": "medium"},
        {"name": "Workspace Service", "type": "service", "complexity": "high"},
        {"name": "Stock API", "type": "api", "complexity": "medium"},
        {"name": "Workspace API", "type": "api", "complexity": "high"},
    ]

    phase_estimate = estimate_phase("Core Services Phase", phase_components)
    print(json.dumps(phase_estimate, indent=2))
