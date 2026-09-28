# YouTube Content Factory

The app creates Story, Fact, News, Music and Visual content through one shared
flow and the same three agents:

```text
Prompt form → Director → Writer → Editor → Export
```

For Story, Editor is called twice: first to score the Writer draft, then once
more to rewrite the full story using that feedback. Other content types use one
Editor rewrite.

Fact and News use model-native web search as part of the Director call. Their
sources and evidence are passed to Writer and Editor so they can preserve
attribution and uncertainty. Visual projects can also use the narration and
blueprint from a completed source project.

## Start

```powershell
Copy-Item .env.example .env
notepad .env
docker compose up -d --build
```

Set `LLM_BASE_URL`, `LLM_API_KEY` and the three `MODEL_*` values in `.env`.
Fact and News also need a search-capable model endpoint; configure it with the
`NATIVE_WEB_SEARCH_*` values. Before generating content, run
`python scripts/preflight.py` to check gateway and search connectivity.

Open `http://localhost:8090` after the service starts.

## Main code paths

- `frontend/src/views/HomeView.vue`: prompt form and generate request.
- `api/main.py`: HTTP routes and project lifecycle.
- `api/service.py`: runs the content flow and exports each language.
- `workflows/router.py`: sends every content type to the shared workflow.
- `workflows/content.py`: calls Director, Writer and Editor in sequence.
- `agents/director`, `agents/writer`, `agents/editor`: the only agent roles.
- `exporters/content.py`: Markdown, JSON, TTS text and rich document exports.

Generated projects live under `outputs/`; the SQLite job database lives under
`data/`.
