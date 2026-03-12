from typing import TYPE_CHECKING, List, Tuple

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from src.integrations.ollama_client import OllamaClient
from src.models.config import Config
from src.models.messages import SlackMessage, ToolResult
from src.prompts.prompt_manager import PromptManager
from src.tools.github_tool import github
from src.tools.opencode_tool import opencode
from src.tools.ollama_tool import ollama_generate

if TYPE_CHECKING:
    from src.integrations.slack_client import SlackClient


class AgentOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.ollama_client = OllamaClient(config)
        self.prompt_manager = PromptManager()
        self.tools = [github, opencode, ollama_generate]
        
        self._agent_executor: AgentExecutor | None = None
    
    @property
    def agent_executor(self) -> AgentExecutor:
        if self._agent_executor is None:
            llm_with_tools = self.ollama_client.bind_tools(self.tools)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "{system_prompt}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            agent = create_tool_calling_agent(llm_with_tools, self.tools, prompt)
            
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=False,
                max_iterations=10,
            )
        
        return self._agent_executor
    
    def process_message(
        self,
        message: SlackMessage,
        slack_client: "SlackClient",
    ):
        from src.integrations.slack_client import SlackClient
        
        initial_response = slack_client.send_message(
            channel=message.channel,
            text="Analyzing your request...",
            thread_ts=message.thread_ts,
        )
        message_ts = initial_response["ts"]
        
        slash_commands = SlackClient.parse_slash_commands(message.text)
        
        if slash_commands:
            self._execute_slash_commands(
                slash_commands=slash_commands,
                slack_client=slack_client,
                channel=message.channel,
                thread_ts=message.thread_ts,
                message_ts=message_ts,
            )
        else:
            self._run_agent(
                user_message=message.text,
                slack_client=slack_client,
                channel=message.channel,
                thread_ts=message.thread_ts,
                message_ts=message_ts,
            )
    
    def _execute_slash_commands(
        self,
        slash_commands: List[Tuple[str, str]],
        slack_client: "SlackClient",
        channel: str,
        thread_ts: str,
        message_ts: str,
    ):
        results: List[ToolResult] = []
        
        for i, (cmd, args) in enumerate(slash_commands, 1):
            slack_client.update_message(
                channel=channel,
                ts=message_ts,
                text=f"Executing command {i}/{len(slash_commands)}: /{cmd} {args[:50]}...",
            )
            
            try:
                if cmd == "git":
                    output = github.invoke(args)
                    success = True
                elif cmd == "opencode":
                    output = opencode.invoke(args)
                    success = True
                else:
                    output = f"Unknown command: {cmd}"
                    success = False
                
                results.append(ToolResult(
                    tool_name=cmd,
                    output=output,
                    success=success,
                ))
                
                if not success:
                    break
                    
            except Exception as e:
                results.append(ToolResult(
                    tool_name=cmd,
                    output=str(e),
                    success=False,
                    error=str(e),
                ))
                break
        
        final_output = self._format_results(results)
        handled_output = slack_client.handle_long_output(
            output=final_output,
            channel=channel,
            thread_ts=thread_ts,
        )
        
        if all(r.success for r in results):
            status_text = f"✅ All commands completed successfully!\n\n{handled_output}"
        else:
            status_text = f"⚠️ Command execution stopped due to failure:\n\n{handled_output}"
        
        slack_client.update_message(
            channel=channel,
            ts=message_ts,
            text=status_text,
        )
    
    def _run_agent(
        self,
        user_message: str,
        slack_client: "SlackClient",
        channel: str,
        thread_ts: str,
        message_ts: str,
    ):
        slack_client.update_message(
            channel=channel,
            ts=message_ts,
            text="Analyzing request and determining which tools to use...",
        )
        
        system_prompt = self.prompt_manager.render_system_prompt(
            user_message=user_message,
            slash_commands=None,
        )
        
        try:
            result = self.agent_executor.invoke({
                "input": user_message,
                "system_prompt": system_prompt,
            })
            
            output = result.get("output", "No output generated")
            
            handled_output = slack_client.handle_long_output(
                output=output,
                channel=channel,
                thread_ts=thread_ts,
            )
            
            slack_client.update_message(
                channel=channel,
                ts=message_ts,
                text=f"✅ Task completed!\n\n{handled_output}",
            )
            
        except Exception as e:
            slack_client.update_message(
                channel=channel,
                ts=message_ts,
                text=f"❌ Error: {str(e)}",
            )
    
    def _format_results(self, results: List[ToolResult]) -> str:
        formatted = []
        for i, result in enumerate(results, 1):
            status = "✅" if result.success else "❌"
            output_preview = result.output[:100] + "..." if len(result.output) > 100 else result.output
            formatted.append(
                f"{status} Command {i}: /{result.tool_name}\n{output_preview}"
            )
        return "\n\n".join(formatted)
