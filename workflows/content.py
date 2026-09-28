from agents.director.agent import agent as director
from agents.editor.agent import agent as editor
from agents.writer.agent import agent as writer
from core.async_utils import gather_cancel_on_error
from core.schemas.output import LanguageOutput,WorkflowResult
from observability.telemetry import telemetry
from storage.files import file_store
from storage.jobs import job_store


async def _visual_source_context(cfg):
    if not cfg.source_project_id:
        return {}
    source=await job_store.get(cfg.source_project_id)
    if not source:
        raise RuntimeError("VISUAL_SOURCE_PROJECT_NOT_FOUND")
    if source.status.value!="completed":
        raise RuntimeError(f"VISUAL_SOURCE_PROJECT_NOT_COMPLETED[{source.status.value}]")
    manifest=file_store.read_json(source.id,"manifest.json",{}) or {}
    blueprint=file_store.read_json(source.id,"shared/blueprint.json",{}) or {}
    languages=source.request.languages or []
    preferred=(cfg.languages or [""])[0]
    language=preferred if preferred in languages else (languages[0] if languages else preferred)
    stem={"fact":"script","story":"story","news":"news_script","music":"suno_prompt"}.get(source.request.niche,"")
    narration=file_store.read_text(source.id,f"{language}/{stem}.md","") if stem and language else ""
    if not narration:
        raise RuntimeError("VISUAL_SOURCE_NARRATION_NOT_READY")
    return {"project_name":source.name,"manifest":manifest,"blueprint":blueprint,
            "niche":source.request.niche,"language":language,"narration":narration}


class ContentWorkflow:
    async def run(self,cfg,request_context=None):
        source_context=await _visual_source_context(cfg) if cfg.niche=="visual" else {}
        await telemetry.step("director","running","Creating the content plan")
        plan=await director.plan(cfg,{
            "request_context":request_context or {},"source_project":source_context,
        })
        await telemetry.step("director","success","Content plan ready")

        async def one(language):
            await telemetry.step("writer","running",f"Writing {language}",language=language)
            draft=(await writer.write(cfg,language,plan)).strip()
            if not draft:
                raise ValueError(f"WRITER_EMPTY_OUTPUT: {language}")
            await telemetry.step("writer","success",f"Draft ready for {language}",language=language)
            review=None
            if cfg.niche=="story":
                await telemetry.step("editor","running",f"Scoring story for {language}",language=language)
                review=await editor.review_story(cfg,language,plan,draft)
                await telemetry.step(
                    "editor","success",f"Story scored {review['overall_score']}/10",language=language,
                )
                await telemetry.step("editor","running",f"Rewriting the complete story for {language}",language=language)
                final=(await editor.rewrite_story(cfg,language,plan,draft,review)).strip()
            else:
                await telemetry.step("editor","running",f"Rewriting complete draft for {language}",language=language)
                final=(await editor.edit(cfg,language,plan,draft)).strip()
            if not final:
                final=draft
            await telemetry.step("editor","success",f"Final content ready for {language}",language=language)
            outline={"content_type":cfg.niche,"director_plan":plan}
            checks={"ready":True,"agent_flow":["director","writer","editor_review","editor_rewrite"] if cfg.niche=="story" else ["director","writer","editor"]}
            if review is not None:
                checks["editor_review"]=review
                checks["editor_score"]=review["overall_score"]
            if cfg.niche in {"fact","news"}:
                checks["research_mode"]="native_web_search"
                checks["source_count"]=len(plan.get("sources",[]))
            return language,LanguageOutput(
                language=language,title=plan.get("title") or cfg.topic[:96],
                outline=outline,draft=draft,final_text=final,checks=checks,
            )

        outputs=dict(await gather_cancel_on_error(*(one(language) for language in cfg.languages)))
        research={}
        if cfg.niche in {"fact","news"}:
            research={"evidence":plan.get("evidence",[]),"sources":plan.get("sources",[]),
                      "claim_ledger":plan.get("evidence",[])}
        await telemetry.step("content_workflow","success","Content workflow complete")
        return WorkflowResult(
            niche=cfg.niche,canonical_title=plan.get("title") or cfg.topic[:96],
            blueprint=plan,research=research,
            outputs=outputs,
        )


workflow=ContentWorkflow()
