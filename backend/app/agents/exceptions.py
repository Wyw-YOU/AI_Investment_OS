"""
Agent 专用异常类。
用于区分 agent 执行错误和系统级错误，方便上层做不同处理。
"""


class AgentExecutionError(Exception):
    """Agent 执行失败的基类，包含 agent 名称和原始错误信息。"""
    def __init__(self, agent_name: str, message: str, original_error: Exception | None = None):
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{agent_name}] {message}")


class AgentTimeoutError(AgentExecutionError):
    """Agent 执行超时（LLM 响应过慢）。"""
    def __init__(self, agent_name: str, timeout: float):
        super().__init__(agent_name, f"Execution timed out after {timeout}s")


class AgentValidationError(AgentExecutionError):
    """Agent 输出格式校验失败（LLM 返回了不符合预期的 JSON）。"""
    def __init__(self, agent_name: str, message: str):
        super().__init__(agent_name, f"Validation error: {message}")
