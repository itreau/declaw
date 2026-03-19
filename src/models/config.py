import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str
    model: str = "qwen2.5-coder:14b"
    backend: str = "opencode"
    max_output_length: int = 200
    output_dir: Path = Path("./output")
    tool_timeout: int = 120
    workspace_dir: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
            slack_signing_secret=os.environ["SLACK_SIGNING_SECRET"],
            slack_app_token=os.environ["SLACK_APP_TOKEN"],
            model=os.getenv("MODEL", "qwen2.5-coder:14b"),
            backend=os.getenv("BACKEND", "opencode"),
            max_output_length=int(os.getenv("MAX_OUTPUT_LENGTH", "200")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            tool_timeout=int(os.getenv("TOOL_TIMEOUT", "120")),
            workspace_dir=os.getenv("WORKSPACE_DIR"),
        )

    def __init__(self, **data):
        super().__init__(**data)
        self.output_dir.mkdir(exist_ok=True)