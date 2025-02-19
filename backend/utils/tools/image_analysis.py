from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


class ImageAnalysisTool:
    def __init__(self, llm: ChatOllama):
        """Initialize image analysis tool with language model"""
        self.llm = llm

    def analyze_image(self, research_topic: str, base64_image: Optional[str] = None) -> Dict[str, Any]:
        """Process and analyze the image input if available"""
        if not base64_image:
            return {}

        try:
            # Use vision model to analyze image
            system_prompt = """Analyze the image and combine it with the user's text input 
            to generate a comprehensive understanding. Focus on technical and relevant details."""

            image_content = f"data:image/jpeg;base64,{base64_image}"
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=[
                    {"type": "text", "text": research_topic},
                    {"type": "image_url", "image_url": image_content}
                ])
            ]

            result = self.llm.invoke(messages)
            return {"running_summary": result.content}
        except Exception as e:
            print(f"Error processing image: {e}")
            return {}
