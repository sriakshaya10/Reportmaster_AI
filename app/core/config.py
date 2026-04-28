from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ReportMaster AI"
    api_v1_prefix: str = "/api/v1"

    data_dir: Path = Path("./data")
    upload_dir: Path = Path("./data/uploads")
    index_dir: Path = Path("./data/index")

    top_k: int = 3
    chunk_size: int = 800
    chunk_overlap: int = 120

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    local_embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
