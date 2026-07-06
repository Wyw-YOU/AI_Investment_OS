class AgentExecutionError(Exception):
    def __init__(self, agent_name: str, message: str, original_error: Exception | None = None):
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{agent_name}] {message}")


class AgentTimeoutError(AgentExecutionError):
    def __init__(self, agent_name: str, timeout: float):
        super().__init__(agent_name, f"Execution timed out after {timeout}s")


class AgentValidationError(AgentExecutionError):
    def __init__(self, agent_name: str, message: str):
        super().__init__(agent_name, f"Validation error: {message}")
