from typing import List, Optional, Tuple
from pydantic import BaseModel


class SlackMessage(BaseModel):
    text: str
    channel: str
    user: str
    ts: Optional[str] = None
    thread_ts: Optional[str] = None


class ToolResult(BaseModel):
    tool_name: str
    output: str
    success: bool
    error: Optional[str] = None


class Command(BaseModel):
    command: str
    args: str


class AgentResponse(BaseModel):
    message: str
    tool_results: List[ToolResult] = []
    requires_file_upload: bool = False
    file_path: Optional[str] = None


ParsedCommands = List[Tuple[str, str]]
