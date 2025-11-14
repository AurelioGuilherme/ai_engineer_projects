import logging
from typing import Any, Callable, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crew")


class Agent:
    def __init__(self, name: str, role_description: str, func: Callable[..., Any]):
        self.name = name
        self.role_description = role_description
        self.func = func

    def run(self, **kwargs):
        logger.info(f"[Agent:{self.name}] Starting task...")
        result = self.func(**kwargs)
        logger.info(f"[Agent:{self.name}] Completed.")
        return result


class Crew:
    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def execute(self, initial_context: Dict = None):
        ctx = initial_context or {}

        for agent in self.agents:
            out = agent.run(context=ctx)
            if isinstance(out, dict):
                ctx.update(out)

        return ctx
