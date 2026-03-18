import json
import re
from typing import TYPE_CHECKING, List, Tuple

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from src.integrations.ollama_client import OllamaClient
from src.models.config import Config
from src.models.messages import SlackMessage, ToolResult
from src.prompts.prompt_manager import PromptManager
from src.tools.github_tool import github
from src.tools.git_tool import git
from src.tools.opencode_tool import opencode
from src.tools.ollama_tool import ollama_generate

if TYPE_CHECKING:
    from src.integrations.slack_client import SlackClient


class AgentOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.ollama_client = OllamaClient(config)
        self.prompt_manager = PromptManager()
        self.tools = [github, git, opencode, ollama_generate]
        
        self._agent_executor: AgentExecutor | None = None
    
    def _parse_json_tool_calls(self, content: str) -> List[Tuple[str, dict]]:
        """Parse JSON tool calls from model output content.
        
        Handles cases where models don't natively support function calling
        and return tool calls as JSON strings in the content.
        
        Args:
            content: The model's output content
            
        Returns:
            List of (tool_name, arguments) tuples
        """
        tool_calls = []
        
        # Try to find JSON objects that look like tool calls
        # Pattern: {"name": "...", "arguments": {...}}
        json_pattern = r'\{[^{}]*"name"[^{}]*:[^{}]*"([^"]+)"[^{}]*"arguments"[^{}]*:[^{}]*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}[^{}]*\}'
        
        matches = re.finditer(json_pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                # Parse the JSON
                json_str = match.group(0)
                tool_call = json.loads(json_str)
                
                if "name" in tool_call and "arguments" in tool_call:
                    tool_name = tool_call["name"]
                    arguments = tool_call["arguments"]
                    
                    # Validate tool name
                    if tool_name in ["github", "git", "opencode", "ollama_generate", "github_tool", "git_tool", "opencode_tool", "ollama_tool"]:
                        # Normalize tool names
                        if tool_name.endswith("_tool"):
                            tool_name = tool_name[:-5]  # Remove "_tool" suffix
                        
                        tool_calls.append((tool_name, arguments))
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[DEBUG] Failed to parse potential tool call: {e}")
                continue
        
        return tool_calls
    
    def _execute_tool_calls_from_content(self, content: str) -> str:
        """Execute tool calls found in content and return results.
        
        Args:
            content: The model's output content
            
        Returns:
            Results from executing tool calls, or original content if no tool calls found
        """
        tool_calls = self._parse_json_tool_calls(content)
        
        if not tool_calls:
            return content
        
        print(f"[DEBUG] Found {len(tool_calls)} tool call(s) in content")
        
        results = []
        for tool_name, arguments in tool_calls:
            try:
                print(f"[DEBUG] Executing tool: {tool_name} with args: {arguments}")
                
                # Get the tool
                tool_map = {
                    "github": github,
                    "git": git,
                    "opencode": opencode,
                    "ollama": ollama_generate,
                }
                
                tool = tool_map.get(tool_name)
                if not tool:
                    results.append(f"Unknown tool: {tool_name}")
                    continue
                
                # Execute the tool with arguments
                if "command" in arguments:
                    output = tool.invoke(arguments["command"])
                elif "prompt" in arguments:
                    output = tool.invoke(arguments["prompt"])
                else:
                    # Try to find any argument
                    args = list(arguments.values())
                    if args:
                        output = tool.invoke(args[0])
                    else:
                        output = f"No arguments provided for tool {tool_name}"
                
                results.append(f"✅ {tool_name}: {output}")
                
            except Exception as e:
                print(f"[ERROR] Tool execution failed: {e}")
                results.append(f"❌ {tool_name}: {str(e)}")
        
        return "\n\n".join(results)
    
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
                handle_parsing_errors=True,
                max_iterations=10,
                max_execution_time=300,
                return_intermediate_steps=True,
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
                    output = git.invoke(args)
                    success = True
                elif cmd == "github":
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
            print(f"[DEBUG] Invoking agent with message: {user_message[:100]}...")
            result = self.agent_executor.invoke({
                "input": user_message,
                "system_prompt": system_prompt,
            })
            
            print(f"[DEBUG] Agent result keys: {result.keys()}")
            
            # Get the output
            if "output" in result:
                output = result["output"]
            elif "intermediate_steps" in result and result["intermediate_steps"]:
                # Extract the last step's output
                last_step = result["intermediate_steps"][-1]
                if len(last_step) >= 2:
                    output = str(last_step[1])
                else:
                    output = "Task completed but no output was generated"
            else:
                output = result.get("output", "No output generated")
            
            # Check if the model returned tool calls as JSON in content
            # This happens when models don't natively support function calling
            output = self._execute_tool_calls_from_content(output)
            
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
            print(f"[ERROR] Agent execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
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
