# YouTube Content Factory

Create Story, Fact, News, Music and Video content through the same four-step
agent flow:

```text
Prompt → Director → Writer → Reviewer → Editor → Export
```

Each project saves a readable `content.md` and a structured `content.json`.
The JSON is used by the API and to reuse a completed project's content as a
video-generation source; it is not just a second copy of the Markdown. Project
pages show agent activity and progress. If generation fails after producing
one or more completed language outputs, those outputs and the error are
preserved in the project files.

## Start

Copy `.env.example` to `.env` and add your OpenAI API key, then run:

```powershell
docker compose up -d --build
```

Open `http://localhost:8090`. Generated files live under `outputs/`; project
records and agent progress live in SQLite under `data/`.

For local development, install the Python dependencies and launch Flask's
development server (WebSocket support is enabled by Flask-Sock):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app api.main:app run --host=127.0.0.1 --port=8090
```

The interface is rendered by Flask templates in `templates/`. Small plain
JavaScript clients in `static/` use WebSockets for live project and list
progress; there is no Node or frontend build step.

The application code is grouped under `service/`; `api/` contains the Flask
request routes, and SQLite is stored in `data/factory.db`.
