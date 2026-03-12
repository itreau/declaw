from pathlib import Path
from typing import List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, Template


class PromptManager:
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
        )
        self._system_prompt_template: Optional[Template] = None
    
    @property
    def system_prompt_template(self) -> Template:
        if self._system_prompt_template is None:
            self._system_prompt_template = self.env.get_template("system_prompt.j2")
        return self._system_prompt_template
    
    def render_system_prompt(
        self,
        user_message: str,
        slash_commands: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        return self.system_prompt_template.render(
            user_message=user_message,
            slash_commands=slash_commands or [],
        )
