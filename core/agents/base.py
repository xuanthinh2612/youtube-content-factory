from pathlib import Path
from core.llm.client import llm
from observability.tracing import trace_agent
from observability.telemetry import telemetry


class BaseAgent:
    name: str = "agent"
    tier: str = "MIDDLE"
    prompt_path: Path | None = None

    def system_prompt(self):
        return self.prompt_path.read_text(encoding="utf-8") if self.prompt_path else ""

    async def text(self,user,temperature=.2,max_tokens=7000,system_prompt=None):
        await telemetry.node_start(self.name, f"model-tier={self.tier}")
        try:
            with trace_agent(self.name,self.tier):
                system=system_prompt if system_prompt is not None else self.system_prompt()
                out=await llm.chat(self.tier,system,user,temperature,max_tokens,node=self.name)
            await telemetry.node_success(self.name)
            return out
        except Exception as exc:
            await telemetry.node_error(self.name,exc)
            raise
