import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    slack_app_token: str = Field(..., env="SLACK_APP_TOKEN")
    ollama_url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    model: str = Field(default="qwen2.5-coder:14b", env="MODEL")
    backend: str = Field(default="opencode", env="BACKEND")
    max_output_length: int = Field(default=200, env="MAX_OUTPUT_LENGTH")
    output_dir: Path = Field(default=Path("./output"), env="OUTPUT_DIR")
    tool_timeout: int = Field(default=120, env="TOOL_TIMEOUT")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    workspace_dir: Optional[str] = Field(default=None, env="WORKSPACE_DIR")

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
            slack_signing_secret=os.environ["SLACK_SIGNING_SECRET"],
            slack_app_token=os.environ["SLACK_APP_TOKEN"],
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("MODEL", "qwen2.5-coder:14b"),
            backend=os.getenv("BACKEND", "opencode"),
            max_output_length=int(os.getenv("MAX_OUTPUT_LENGTH", "200")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            tool_timeout=int(os.getenv("TOOL_TIMEOUT", "120")),
            github_token=os.getenv("GITHUB_TOKEN"),
            workspace_dir=os.getenv("WORKSPACE_DIR"),
        )

    def __init__(self, **data):
        super().__init__(**data)
        self.output_dir.mkdir(exist_ok=True)
