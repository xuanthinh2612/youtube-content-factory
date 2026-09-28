# Architecture

All content types use the same linear agent flow:

```text
Director → Writer → Editor → Export
```

The Director turns the form input into a concise plan. For Story, that plan
lists the premise and major events, shaped to the requested duration. For Fact
and News, the Director uses model-native web search and returns source-backed
evidence with the plan. The Writer drafts from the plan and requested duration.

For Story, the Editor first scores naturalness, hook, logic, pacing, character
consistency and duration fit. It then rewrites the complete story once using
that feedback. The scores are shown with the project output. Other content
types use one Editor rewrite. There are no retry, repair or further review
loops in the content workflow.

## Request path

1. `frontend/src/views/HomeView.vue` sends the form to `/api/generate`.
2. `api/main.py` validates the request and queues a project.
3. `api/service.py` calls `workflows/router.py`.
4. `workflows/content.py` calls `agents/director`, then `agents/writer`, then
   `agents/editor` for each requested language.
5. `api/service.py` sends the final text to `exporters/content.py` and records
   project metadata and usage.

`core/workflow/graphs.py` describes the same order for the project monitor.

## Content-specific context

The three roles are shared across Story, Fact, News, Music and Visual. Their
prompts use the content type to shape the plan, draft and rewrite. Fact and News
preserve citations, attribution and uncertainty. Music produces a copy-ready
music-generation prompt. Visual produces a scene-by-scene plan and can use the
narration and blueprint of a completed source project.

## Runtime support

The FastAPI service stores jobs in SQLite, exports files beneath `outputs/`,
and reports events, usage and failures through the existing observability
modules. Model tier selection and finite network retries are configured in
`core/config.py`.
