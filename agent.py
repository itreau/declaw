from src.integrations.slack_client import SlackClient
from src.models.config import Config
from src.orchestrator import AgentOrchestrator


def main():
    config = Config.from_env()
    orchestrator = AgentOrchestrator(config)
    slack_client = SlackClient(config, orchestrator)
    
    print("Starting PyAgent with LangChain orchestration...")
    print(f"Backend: {config.backend}")
    print(f"Model: {config.model}")
    print(f"Max output length: {config.max_output_length}")
    print(f"Output directory: {config.output_dir}")
    print("Ready to receive messages!")
    
    slack_client.start()


if __name__ == "__main__":
    main()
