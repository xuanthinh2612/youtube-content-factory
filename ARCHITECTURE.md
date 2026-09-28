# Architecture

The Flask request layer in `api/` renders pages and exposes the JSON API. It
delegates project operations and runtime work to `service/`.

```text
api/        Flask request routes
data/       SQLite database
service/    agents, workflows, storage, exports, telemetry and project runtime
tests/      Python tests
templates/  server-rendered HTML
static/     CSS and the small WebSocket status client
outputs/    generated project files
```

For each requested language, `service/workflows/content_generation.py` runs the same
sequential flow: Director → Writer → Reviewer → Editor. The selected content
type supplies the agent functions, and their prompts live in
`service/agents/prompts/`. `service/agents/role_execution.py` shares the role-call
logic; the LLM client, settings and project models live directly under
`service/`.

The service runs its asyncio project queue on a dedicated loop while Gunicorn
serves Flask with threaded workers. Flask-Sock streams project snapshots and
new activity events over `/ws/projects/<project_id>` and status snapshots over
`/ws/projects`. The project and project-list pages update without reloading.
Project activity logs show each LLM response and failures.

Generated Markdown is sanitized before rendering. SQLite project and event
records live in `data/factory.db`; generated project files live in `outputs/`.
Each project exports Markdown for people and JSON for structured consumers,
including the API and video generation from an existing project. The many
other JSON files in an output folder are runtime artifacts, not source modules
or extra dependencies.
