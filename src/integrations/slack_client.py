import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.models.config import Config
from src.models.messages import SlackMessage

if TYPE_CHECKING:
    from src.orchestrator import AgentOrchestrator


class SlackClient:
    def __init__(self, config: Config, orchestrator: "AgentOrchestrator"):
        self.config = config
        self.orchestrator = orchestrator
        self.app = App(token=config.slack_bot_token)
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.app.event("app_mention")
        def handle_mention(body, client):
            event = body["event"]
            message = SlackMessage(
                text=event["text"],
                channel=event["channel"],
                user=event["user"],
                ts=event.get("ts"),
                thread_ts=event.get("thread_ts") or event.get("ts"),
            )
            self.orchestrator.process_message(message, self)
    
    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
    ) -> dict:
        kwargs = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        return self.app.client.chat_postMessage(**kwargs)
    
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
    ) -> dict:
        return self.app.client.chat_update(
            channel=channel,
            ts=ts,
            text=text,
        )
    
    def upload_file(
        self,
        channel: str,
        file_path: Path,
        initial_comment: str,
        thread_ts: Optional[str] = None,
    ) -> dict:
        kwargs = {
            "channel": channel,
            "file": str(file_path),
            "title": file_path.name,
            "initial_comment": initial_comment,
        }
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        return self.app.client.files_upload_v2(**kwargs)
    
    def handle_long_output(
        self,
        output: str,
        channel: str,
        thread_ts: Optional[str] = None,
    ) -> str:
        if len(output) <= self.config.max_output_length:
            return output
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}.txt"
        filepath = self.config.output_dir / filename
        
        with open(filepath, "w") as f:
            f.write(output)
        
        try:
            self.upload_file(
                channel=channel,
                file_path=filepath,
                initial_comment=f"Output exceeded {self.config.max_output_length} characters:",
                thread_ts=thread_ts,
            )
            return f"Output exceeded {self.config.max_output_length} characters. See attached file: {filename}"
        except Exception as e:
            return f"Output saved locally to {filepath} (Slack upload failed: {str(e)})"
    
    @staticmethod
    def parse_slash_commands(message: str) -> List[Tuple[str, str]]:
        commands = []
        parts = re.split(r"(?=/git\s|/opencode\s)", message)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith("/git "):
                command = "git"
                args = part[5:].strip()
                commands.append((command, args))
            elif part.startswith("/opencode "):
                command = "opencode"
                args = part[10:].strip()
                commands.append((command, args))
            elif part.startswith("/git\n") or part.startswith("/git\t"):
                command = "git"
                args = part[4:].strip()
                commands.append((command, args))
            elif part.startswith("/opencode\n") or part.startswith("/opencode\t"):
                command = "opencode"
                args = part[9:].strip()
                commands.append((command, args))
        
        return commands
    
    def start(self):
        handler = SocketModeHandler(self.app, self.config.slack_app_token)
        handler.start()
