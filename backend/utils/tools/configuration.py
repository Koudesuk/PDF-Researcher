from dataclasses import dataclass, field, fields
from langchain_core.runnables import RunnableConfig
from typing import Any, Optional


@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the research assistant."""
    max_web_research_loops: int = 3
    image_llm: str = "llama3.2-vision"
    research_llm: str = "phi4"
    chat_with_picture: bool = False
    web_research: bool = False

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: configurable.get(f.name)
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v is not None})
