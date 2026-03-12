import requests

from langchain.tools import tool

from src.models.config import Config


@tool
def ollama_generate(prompt: str) -> str:
    """Generate text using Ollama LLM.
    
    Use this tool for:
    - Explanations and documentation
    - General questions and answers
    - Brainstorming ideas
    - Code explanations
    - Writing documentation
    - Any text generation task
    
    Args:
        prompt: The prompt to send to Ollama
    
    Returns:
        Generated text from Ollama
        
    Examples:
        ollama_generate("explain how async/await works in Python")
        ollama_generate("write documentation for this API endpoint")
        ollama_generate("suggest improvements for this code")
        ollama_generate("what are the best practices for error handling?")
    """
    config = Config.from_env()
    
    try:
        response = requests.post(
            f"{config.ollama_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=config.tool_timeout,
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {str(e)}")
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"Failed to parse Ollama response: {str(e)}")
