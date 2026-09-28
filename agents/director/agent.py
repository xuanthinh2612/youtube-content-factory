from datetime import datetime,timezone

from core.agents.base import BaseAgent
from core.agents.prompt import prompt_file
from core.config import settings
from core.llm.web_search import native_web_search


SEARCH_PLAN_SCHEMA={
    "type":"object","required":["title","plan","evidence"],"additionalProperties":False,
    "properties":{
        "title":{"type":"string"},
        "plan":{"type":"string"},
        "evidence":{"type":"array","items":{
            "type":"object","required":["claim","status","source_urls"],"additionalProperties":False,
            "properties":{"claim":{"type":"string"},"status":{"type":"string"},
                          "source_urls":{"type":"array","items":{"type":"string"}}}
        }},
    },
}


class DirectorAgent(BaseAgent):
    name="director"
    tier=settings.tier_director
    prompt_path=prompt_file(__file__)

    async def plan(self,cfg,context):
        language=(cfg.languages or ["vi"])[0]
        user=(
            f"CONTENT_TYPE:{cfg.niche}\nUSER_PROMPT:{cfg.topic}\n"
            f"LANGUAGE:{language}\nDURATION_MINUTES:{cfg.duration_minutes}\n"
            f"STYLE:{cfg.style}\nTONE:{cfg.tone}\nAUDIENCE:{cfg.audience}\n"
            f"EXTRA_INSTRUCTIONS:{cfg.extra_instructions}\n"
            f"PROJECT_CONTEXT:{context}\n"
        )
        if cfg.niche=="story":
            user+=(
                "STORY_OUTLINE_REQUIREMENTS: Give the story title and premise, then an ordered outline "
                "of the major events. Make the events causal and cover the opening hook, character goals, "
                "turning points, climax and resolution. Scale the number and development of events to "
                f"the requested {cfg.duration_minutes}-minute story. Do not write finished scenes or prose.\n"
            )
        if cfg.niche in {"fact","news"}:
            current_date=datetime.now(timezone.utc).date().isoformat()
            response=await native_web_search.search_json(
                tier=settings.tier_director,
                system=self.system_prompt()+"\nUse native web search. Cite only URLs returned in search citations. "
                    "Create a concise plan and list the key source-backed evidence.",
                user=user+f"CURRENT_DATE:{current_date}\nTIMEZONE:{cfg.timezone or settings.project_timezone}\n",
                node=self.name,error_code=f"{cfg.niche.upper()}_SEARCH_UNAVAILABLE",
                invalid_output_code=f"{cfg.niche.upper()}_DIRECTOR_OUTPUT_INVALID",
                required_keys=("title","plan","evidence"),schema=SEARCH_PLAN_SCHEMA,
                max_tokens=7000,
            )
            return {**response.data,"sources":response.citations,"current_date":current_date}

        plan=await self.text(user,temperature=.45,max_tokens=7000)
        return {"title":cfg.topic[:96].strip(),"plan":plan,"evidence":[],"sources":[]}


agent=DirectorAgent()
