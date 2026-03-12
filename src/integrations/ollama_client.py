from typing import List

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.models.config import Config


class OllamaClient:
    def __init__(self, config: Config):
        self.config = config
        self._llm: ChatOllama | None = None
    
    @property
    def llm(self) -> ChatOllama:
        if self._llm is None:
            self._llm = ChatOllama(
                model=self.config.model,
                base_url=self.config.ollama_url,
                temperature=0,
            )
        return self._llm
    
    def bind_tools(self, tools: List):
        return self.llm.bind_tools(tools)
    
    def invoke(self, messages: List[BaseMessage]) -> BaseMessage:
        return self.llm.invoke(messages)
    
    def create_messages(
        self,
        system_prompt: str,
        user_message: str,
    ) -> List[BaseMessage]:
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
