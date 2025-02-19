import operator
from dataclasses import dataclass, field
from typing_extensions import TypedDict, Annotated


@dataclass(kw_only=True)
class SummaryState:
    research_topic: str = field(default=None)  # User input topic/prompt
    search_query: str = field(default=None)  # Generated search query
    web_research_results: Annotated[list, operator.add] = field(
        default_factory=list)  # Research results from web
    sources_gathered: Annotated[list, operator.add] = field(
        default_factory=list)  # Gathered sources
    research_loop_count: int = field(default=0)  # Track research iterations
    running_summary: str = field(default=None)  # Current summary
    base64_image: str = field(default=None)  # Base64 encoded image if any
    enable_web_research: bool = field(default=False)  # Web research flag
    enable_chat_with_picture: bool = field(default=False)  # Image chat flag
    pdf_filename: str = field(default=None)  # PDF filename for FAISS search
    faiss_results: Annotated[list, operator.add] = field(
        default_factory=list)  # Results from FAISS search


@dataclass(kw_only=True)
class SummaryStateInput(TypedDict):
    research_topic: str = field(default=None)  # Initial user input
    enable_web_research: bool = field(default=False)  # Web research flag
    enable_chat_with_picture: bool = field(default=False)  # Image chat flag
    base64_image: str = field(default=None)  # Base64 encoded image if any
    pdf_filename: str = field(default=None)  # PDF filename for FAISS search


@dataclass(kw_only=True)
class SummaryStateOutput(TypedDict):
    running_summary: str = field(default=None)  # Final response/summary
