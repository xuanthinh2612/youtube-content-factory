from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_base_url: str = "http://host.docker.internal:8000/v1"
    llm_api_key: str = "change-me"
    model_fast: str = "fast-model"
    model_middle: str = "middle-model"
    model_hard: str = "hard-model"
    native_web_search_model: str = ""
    native_web_search_fallback_model: str = ""
    native_web_search_mode: str = "auto"  # auto | xai_chat | openai_chat | disabled
    native_web_search_base_url: str = ""
    native_web_search_api_key: str = ""
    native_web_search_max_results: int = 12
    native_web_search_context_size: str = "high"
    native_web_search_require_citations: bool = True
    enable_model_tier_fallback: bool = True
    llm_retry_attempts: int = 3

    # The same three roles are used for every content type.
    tier_director: str = "HARD"
    tier_writer: str = "HARD"
    tier_editor: str = "HARD"

    # Finite network retries are bounded independently from background service loops.
    max_loop_rounds: int = 2
    max_concurrent_projects: int = 2
    max_concurrent_llm_calls: int = 4
    db_path: str = "./data/factory.db"
    data_dir: str = "./outputs"
    log_level: str = "INFO"

    project_timezone: str = "Asia/Tokyo"
    host: str = "127.0.0.1"
    port: int = 8090

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def cap_rounds(self, requested: int | None = None) -> int:
        """Hard cap for finite network retry loops."""
        global_cap=max(1, int(self.max_loop_rounds))
        if requested is None:
            return global_cap
        return min(global_cap, max(1, int(requested)))

    def model_for_tier(self, tier: str) -> str:
        tier = (tier or "MIDDLE").upper()
        if tier == "FAST":
            return self.model_fast
        if tier == "HARD":
            return self.model_hard
        return self.model_middle

    def fallback_tiers(self, tier: str) -> list[str]:
        tier = (tier or "MIDDLE").upper()
        if not self.enable_model_tier_fallback:
            return [tier]
        return {
            "HARD": ["HARD", "MIDDLE", "FAST"],
            "MIDDLE": ["MIDDLE", "FAST"],
            "FAST": ["FAST"],
        }.get(tier, ["MIDDLE", "FAST"])

    def output_dir(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def runtime_url(self,value:str) -> str:
        """Make Docker-host URLs usable when the backend runs directly on host.

        The sample configuration is Docker-first and therefore uses
        ``host.docker.internal``.  That name is not consistently resolvable by a
        host Python process (notably on Windows), even though the same service is
        available at localhost.  Inside a container the configured URL is kept.
        """
        raw=str(value or "").strip()
        if not raw or Path("/.dockerenv").exists():
            return raw
        parsed=urlsplit(raw)
        if (parsed.hostname or "").lower() != "host.docker.internal":
            return raw
        port=f":{parsed.port}" if parsed.port else ""
        return urlunsplit((parsed.scheme,f"127.0.0.1{port}",parsed.path,parsed.query,parsed.fragment))

    def llm_url(self) -> str:
        return self.runtime_url(self.llm_base_url)

    def native_web_search_url(self) -> str:
        return self.runtime_url(self.native_web_search_base_url or self.llm_base_url)

    def native_web_search_key(self) -> str:
        return self.native_web_search_api_key or self.llm_api_key

    def database_path(self) -> Path:
        p = Path(self.db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
