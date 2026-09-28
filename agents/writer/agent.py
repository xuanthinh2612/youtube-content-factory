import json

from core.agents.base import BaseAgent
from core.agents.prompt import prompt_file
from core.config import settings
from quality.validators.duration import length_target


class WriterAgent(BaseAgent):
    name="writer"
    tier=settings.tier_writer
    prompt_path=prompt_file(__file__)

    async def write(self,cfg,language,plan):
        duration_guidance=""
        if cfg.niche=="story":
            target=length_target(language,cfg.duration_minutes*60)
            duration_guidance=(
                f"APPROXIMATE_SPOKEN_LENGTH:{target['minimum']}-{target['maximum']} "
                f"{target['metric']} for about {cfg.duration_minutes} minutes. "
                "Develop the outline fully enough to reach this scale without padding.\n"
            )
        user=(
            f"CONTENT_TYPE:{cfg.niche}\nLANGUAGE:{language}\nUSER_PROMPT:{cfg.topic}\n"
            f"DURATION_MINUTES:{cfg.duration_minutes}\n{duration_guidance}STYLE:{cfg.style}\nTONE:{cfg.tone}\n"
            f"AUDIENCE:{cfg.audience}\nEXTRA_INSTRUCTIONS:{cfg.extra_instructions}\n"
            f"MUSIC_PROVIDER:{cfg.music_provider}\nASPECT_RATIO:{cfg.aspect_ratio}\n"
            f"DIRECTOR_PLAN_AND_EVIDENCE:{json.dumps(plan,ensure_ascii=False)}"
        )
        return await self.text(user,temperature=.55,max_tokens=24000)


agent=WriterAgent()
