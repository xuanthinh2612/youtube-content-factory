from workflows.content import workflow as content_workflow


def director_request_context(cfg):
    defaults={
        "story":("story","natural storytelling"),
        "fact":("fact","clear factual narration"),
        "news":("news","clear current-news narration"),
        "music":("song","original music-generation prompt"),
        "visual":("visual","cinematic visual plan"),
    }
    sub_niche,style=defaults.get(cfg.niche,(cfg.niche,"natural narration"))
    return {
        "interpreted_goal":cfg.topic,
        "sub_niche":cfg.sub_niche or sub_niche,
        "style":cfg.style or style,
        "tone":cfg.tone or "engaging",
        "audience":cfg.audience or "general audience",
    }


def apply_request_defaults(cfg,context=None):
    context=context or director_request_context(cfg)
    if not cfg.sub_niche:
        cfg.sub_niche=context.get("sub_niche","")
    if not cfg.style:
        cfg.style=context.get("style","")
    if not cfg.tone:
        cfg.tone=context.get("tone","")
    if not cfg.audience:
        cfg.audience=context.get("audience","")
    return cfg


async def run_request(cfg,context=None):
    context=context or director_request_context(cfg)
    apply_request_defaults(cfg,context)
    return await content_workflow.run(cfg,request_context=context)
