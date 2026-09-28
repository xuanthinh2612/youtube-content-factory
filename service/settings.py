from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    openai_api_key: str = ""

    max_concurrent_projects: int = 2
    db_path: str = "./data/factory.db"
    data_dir: str = "./outputs"
    log_level: str = "INFO"

    host: str = "127.0.0.1"
    port: int = 8090

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def generated_output_directory(self) -> Path:
        output_directory = Path(self.data_dir)
        output_directory.mkdir(parents=True, exist_ok=True)
        return output_directory

    def sqlite_database_file(self) -> Path:
        database_file = Path(self.db_path)
        database_file.parent.mkdir(parents=True, exist_ok=True)
        return database_file


app_settings = ApplicationSettings()
