from typing import Dict, Any, List
import json
from tavily import TavilyClient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


class WebSearchTool:
    def __init__(self, llm: ChatOllama, llm_json: ChatOllama):
        """Initialize web search tool with language models"""
        self.tavily_client = None
        self.llm = llm
        self.llm_json = llm_json
        self.init_tavily_client()

    def init_tavily_client(self):
        """Initialize Tavily API client"""
        try:
            with open('config/Tavily_API_KEY.txt', 'r') as f:
                api_key = f.read().strip()
            self.tavily_client = TavilyClient(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Tavily client: {e}")

    def generate_query(self, research_topic: str, query_writer_instructions: str) -> Dict[str, Any]:
        """Generate a search query based on the research topic"""
        try:
            query_prompt = query_writer_instructions.format(
                research_topic=research_topic
            )
            result = self.llm_json.invoke([
                SystemMessage(content=query_prompt),
                HumanMessage(content="Generate a query for web search:")
            ])

            query_data = json.loads(result.content)
            return {"search_query": query_data['query']}
        except Exception as e:
            print(f"Error generating query: {e}")
            return {}

    def perform_web_search(self, search_query: str, research_loop_count: int) -> Dict[str, Any]:
        """Perform web research using Tavily"""
        try:
            search_results = self.tavily_client.search(
                search_query,
                search_depth="advanced",
                max_results=3
            )

            # Format sources
            sources = [f"* {result['title']}: {result['url']}"
                       for result in search_results['results']]

            return {
                "sources_gathered": sources,
                "web_research_results": [self._format_results(search_results)],
                "research_loop_count": research_loop_count + 1
            }
        except Exception as e:
            print(f"Error performing web research: {e}")
            return {}

    def _format_results(self, search_results: Dict[str, Any]) -> str:
        """Format search results for summarization"""
        formatted_text = "Sources:\n\n"
        for result in search_results['results']:
            formatted_text += f"Source: {result['title']}\n"
            formatted_text += f"URL: {result['url']}\n"
            formatted_text += f"Content: {result['content']}\n\n"
        return formatted_text
