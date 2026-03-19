from typing import Optional
from pydantic import BaseModel


class SlackMessage(BaseModel):
    text: str
    channel: str
    user: str
    ts: Optional[str] = None
    thread_ts: Optional[str] = None