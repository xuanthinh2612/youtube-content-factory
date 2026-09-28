from pathlib import Path
def prompt_file(agent_file: str) -> Path:
    return Path(agent_file).resolve().with_name("prompt.md")
