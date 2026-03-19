from typing import TYPE_CHECKING

from src.models.config import Config
from src.models.messages import SlackMessage
from src.prompts.prompt_manager import PromptManager
from src.tools.opencode_tool import opencode

if TYPE_CHECKING:
    from src.integrations.slack_client import SlackClient


class AgentOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.prompt_manager = PromptManager()
    
    def process_message(
        self,
        message: SlackMessage,
        slack_client: "SlackClient",
    ):
        initial_response = slack_client.send_message(
            channel=message.channel,
            text="Processing your request...",
            thread_ts=message.thread_ts,
        )
        message_ts = initial_response["ts"]
        
        try:
            system_context = self.prompt_manager.render_system_prompt(
                user_message=message.text,
            )
            combined_prompt = f"{system_context}\n\nUser message: {message.text}"
            output = opencode.invoke(combined_prompt)
            
            handled_output = slack_client.handle_long_output(
                output=output,
                channel=message.channel,
                thread_ts=message.thread_ts,
            )
            
            slack_client.update_message(
                channel=message.channel,
                ts=message_ts,
                text=f"✅ Task completed!\n\n{handled_output}",
            )
        
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] OpenCode execution failed: {error_msg}")
            slack_client.update_message(
                channel=message.channel,
                ts=message_ts,
                text=f"❌ Error: {error_msg}",
            )