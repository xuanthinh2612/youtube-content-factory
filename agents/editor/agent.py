import json

from core.agents.base import BaseAgent
from core.agents.prompt import prompt_file
from core.config import settings
from core.llm.structured import parse_json_object


STORY_REVIEW_FIELDS=(
    "naturalness","hook","logic","pacing","character_consistency","duration_fit",
)
STORY_REVIEW_SCHEMA={
    "type":"object",
    "required":[*STORY_REVIEW_FIELDS,"strengths","issues","revision_brief"],
    "additionalProperties":False,
    "properties":{
        **{name:{"type":"integer","minimum":1,"maximum":10} for name in STORY_REVIEW_FIELDS},
        "strengths":{"type":"array","items":{"type":"string"},"maxItems":5},
        "issues":{"type":"array","items":{"type":"string"},"maxItems":8},
        "revision_brief":{"type":"string","maxLength":2500},
    },
}


class EditorAgent(BaseAgent):
    name="editor"
    tier=settings.tier_editor
    prompt_path=prompt_file(__file__)

    async def edit(self,cfg,language,plan,draft):
        user=(
            f"CONTENT_TYPE:{cfg.niche}\nLANGUAGE:{language}\nUSER_PROMPT:{cfg.topic}\n"
            f"STYLE:{cfg.style}\nTONE:{cfg.tone}\nEXTRA_INSTRUCTIONS:{cfg.extra_instructions}\n"
            f"DIRECTOR_PLAN_AND_EVIDENCE:{json.dumps(plan,ensure_ascii=False)}\n"
            f"COMPLETE_DRAFT_TO_REWRITE:\n{draft}"
        )
        return await self.text(user,temperature=.3,max_tokens=24000)

    async def review_story(self,cfg,language,plan,draft):
        user=(
            f"CONTENT_TYPE:story\nLANGUAGE:{language}\nUSER_PROMPT:{cfg.topic}\n"
            f"DURATION_MINUTES:{cfg.duration_minutes}\nSTYLE:{cfg.style}\nTONE:{cfg.tone}\n"
            f"DIRECTOR_OUTLINE:\n{json.dumps(plan,ensure_ascii=False)}\n"
            f"COMPLETE_WRITER_DRAFT:\n{draft}"
        )
        system=(
            "You are reviewing a complete story draft. Score each dimension from 1 to 10: "
            "naturalness (spoken, human prose), hook (opening interest), logic (causal coherence), "
            "pacing (scene progression), character_consistency (motivations and actions), and "
            "duration_fit (amount of developed story for the requested duration). Give concise "
            "strengths and specific issues, then a short revision_brief for rewriting. Scores must "
            "be whole JSON integers from 1 to 10. Return exactly one JSON object with the requested "
            "fields and no surrounding commentary. Do not rewrite the story in this review."
        )
        raw=await self.text(user,temperature=.1,max_tokens=3500,system_prompt=system)
        review=parse_json_object(raw,required=STORY_REVIEW_SCHEMA["required"],schema=STORY_REVIEW_SCHEMA)
        review["overall_score"]=round(sum(review[name] for name in STORY_REVIEW_FIELDS)/len(STORY_REVIEW_FIELDS),1)
        return review

    async def rewrite_story(self,cfg,language,plan,draft,review):
        user=(
            f"CONTENT_TYPE:story\nLANGUAGE:{language}\nUSER_PROMPT:{cfg.topic}\n"
            f"DURATION_MINUTES:{cfg.duration_minutes}\nSTYLE:{cfg.style}\nTONE:{cfg.tone}\n"
            f"DIRECTOR_OUTLINE:\n{json.dumps(plan,ensure_ascii=False)}\n"
            f"EDITOR_SCORE_AND_FEEDBACK:\n{json.dumps(review,ensure_ascii=False)}\n"
            f"COMPLETE_STORY_TO_REWRITE:\n{draft}"
        )
        system=(
            "You are rewriting a complete story after reviewing it. Rewrite the entire story once. "
            "Use the Editor's scores and revision brief to improve naturalness, opening hook, logic, "
            "pacing, character consistency and fit to the requested duration. Follow the Director's "
            "major events and the user's prompt. Preserve effective parts while improving weak ones. "
            "Return only the complete final story, with no review or editing notes."
        )
        return await self.text(user,temperature=.35,max_tokens=24000,system_prompt=system)


agent=EditorAgent()
