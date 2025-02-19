from typing import Optional, Dict, Any
import json
import time
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .tools.configuration import Configuration
from .tools.state import SummaryState, SummaryStateInput, SummaryStateOutput
from .tools.prompts import (
    query_writer_instructions,
    summarizer_instructions,
    reflection_instructions,
    final_summarize_instructions
)
from .tools.web_search import WebSearchTool
from .tools.image_analysis import ImageAnalysisTool
from .tools.faiss_search import FAISSSearchTool

# 創建rich console實例
console = Console()

# TODO: Optimize the LLM response speed if possible


class ResearchAgent:
    def __init__(self):
        """Initialize the Research Agent with necessary components"""
        self.configuration = Configuration()
        self.research_llm = ChatOllama(model=self.configuration.research_llm)
        self.research_llm_json = ChatOllama(
            model=self.configuration.research_llm, format="json")
        self.image_llm = ChatOllama(model=self.configuration.image_llm)

        # Initialize tools
        self.web_search_tool = WebSearchTool(
            self.research_llm, self.research_llm_json)
        self.image_analysis_tool = ImageAnalysisTool(self.image_llm)
        self.faiss_search_tool = FAISSSearchTool()

        self.graph = self._build_graph()

    def process_input(self, user_input: str, image_data: Optional[str] = None,
                      enable_web_research: bool = False,
                      enable_chat_with_picture: bool = False,
                      pdf_filename: Optional[str] = None) -> Dict[str, Any]:
        """Process user input and optional image data"""
        inputs = {
            "research_topic": user_input,
            "enable_web_research": enable_web_research,
            "enable_chat_with_picture": enable_chat_with_picture,
            "base64_image": image_data,
            "pdf_filename": pdf_filename
        }

        # Create a progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Processing input...", total=None)
            start_time = time.time()

            # Execute the graph with inputs
            result = self.graph.invoke(inputs)

            end_time = time.time()
            elapsed = end_time - start_time
            progress.update(task, completed=True)

            # Display execution time
            console.print(Panel(f"[green]Total execution time: {elapsed:.2f} seconds",
                                title="Performance Metrics",
                                border_style="green"))

        return result

    def _build_graph(self) -> StateGraph:
        """Build the state graph for the research process"""
        builder = StateGraph(SummaryState,
                             input=SummaryStateInput,
                             output=SummaryStateOutput)

        # Add nodes
        builder.add_node("process_image", self._process_image)
        builder.add_node("generate_query", self._generate_query)
        builder.add_node("web_research", self._web_research)
        builder.add_node("summarize_sources", self._summarize_sources)
        builder.add_node("reflect_on_summary", self._reflect_on_summary)
        builder.add_node("search_faiss", self._search_faiss)
        builder.add_node("finalize_summary", self._finalize_summary)

        # Add edges
        builder.add_edge(START, "process_image")
        builder.add_edge("process_image", "generate_query")
        builder.add_edge("generate_query", "web_research")
        builder.add_edge("web_research", "summarize_sources")
        builder.add_edge("summarize_sources", "reflect_on_summary")
        builder.add_conditional_edges(
            "reflect_on_summary",
            self._route_research,
            {
                "continue_research": "web_research",
                "finalize": "search_faiss"
            }
        )
        builder.add_edge("search_faiss", "finalize_summary")
        builder.add_edge("finalize_summary", END)

        return builder.compile()

    def _process_image(self, state: SummaryState) -> Dict[str, Any]:
        """Process image input using ImageAnalysisTool"""
        console.print("[yellow]正在運行圖片處理分支...[/yellow]")
        start_time = time.time()

        if not state.enable_chat_with_picture or not state.base64_image:
            result = {}
        else:
            result = self.image_analysis_tool.analyze_image(
                state.research_topic,
                state.base64_image
            )

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]圖片處理完成[/cyan]\n處理時間: {elapsed:.2f} 秒",
                            title="Image Processing",
                            border_style="blue"))

        return result

    def _generate_query(self, state: SummaryState) -> Dict[str, Any]:
        """Generate search query using WebSearchTool"""
        console.print("[yellow]正在運行查詢生成分支...[/yellow]")
        start_time = time.time()

        if not state.enable_web_research:
            result = {}
        else:
            result = self.web_search_tool.generate_query(
                state.research_topic,
                query_writer_instructions
            )

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]查詢生成完成[/cyan]\n生成時間: {elapsed:.2f} 秒\n生成的查詢: {result.get('search_query', 'N/A')}",
                            title="Query Generation",
                            border_style="blue"))

        return result

    def _web_research(self, state: SummaryState) -> Dict[str, Any]:
        """Perform web research using WebSearchTool"""
        console.print("[yellow]正在運行網頁搜索分支...[/yellow]")
        start_time = time.time()

        if not state.enable_web_research or not state.search_query:
            result = {}
        else:
            result = self.web_search_tool.perform_web_search(
                state.search_query,
                state.research_loop_count
            )

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]網頁搜索完成[/cyan]\n搜索時間: {elapsed:.2f} 秒\n搜索循環次數: {state.research_loop_count}",
                            title="Web Research",
                            border_style="blue"))

        return result

    def _summarize_sources(self, state: SummaryState) -> Dict[str, Any]:
        """Summarize gathered information"""
        console.print("[yellow]正在運行資料總結分支...[/yellow]")
        start_time = time.time()

        if state.web_research_results:
            content = state.web_research_results[-1]
            existing_summary = state.running_summary or ""

            prompt = (f"Extend the existing summary: {existing_summary}\n\n"
                      f"Include new search results: {content}\n"
                      f"That addresses the following topic: {state.research_topic}")

            result = self.research_llm.invoke([
                SystemMessage(content=summarizer_instructions),
                HumanMessage(content=prompt)
            ])

            result_dict = {"running_summary": result.content}
        else:
            result_dict = {
                "running_summary": state.running_summary or state.research_topic}

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]資料總結完成[/cyan]\n處理時間: {elapsed:.2f} 秒",
                            title="Source Summarization",
                            border_style="blue"))

        return result_dict

    def _reflect_on_summary(self, state: SummaryState) -> Dict[str, Any]:
        """Reflect on the current summary and determine next steps"""
        console.print("[yellow]正在運行總結反思分支...[/yellow]")
        start_time = time.time()

        if not state.enable_web_research:
            result = {}
        else:
            try:
                reflection_prompt = reflection_instructions.format(
                    research_topic=state.research_topic
                )
                result = self.research_llm_json.invoke([
                    SystemMessage(content=reflection_prompt),
                    HumanMessage(
                        content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}")
                ])

                reflection_data = json.loads(result.content)
                result = {"search_query": reflection_data['follow_up_query']}
            except Exception as e:
                console.print(f"[red]Error reflecting on summary: {e}[/red]")
                result = {}

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]總結反思完成[/cyan]\n處理時間: {elapsed:.2f} 秒",
                            title="Reflection Analysis",
                            border_style="blue"))

        return result

    def _route_research(self, state: SummaryState) -> str:
        """Determine whether to continue research or finalize"""
        console.print("[yellow]正在運行路由決策分支...[/yellow]")

        if (state.enable_web_research and
                state.research_loop_count < self.configuration.max_web_research_loops):
            decision = "continue_research"
        else:
            decision = "finalize"

        console.print(Panel(f"[cyan]決策完成[/cyan]\n選擇路徑: {decision}",
                            title="Research Routing",
                            border_style="blue"))

        return decision

    def _search_faiss(self, state: SummaryState) -> Dict[str, Any]:
        """Search in FAISS vector database"""
        console.print("[yellow]正在運行向量資料庫搜索分支...[/yellow]")
        start_time = time.time()

        if not state.pdf_filename:
            console.print("[yellow]未提供PDF檔名，跳過向量資料庫搜索[/yellow]")
            return {"faiss_results": []}

        try:
            # 使用當前摘要作為搜索查詢
            results = self.faiss_search_tool.search_similar_content(
                query=state.running_summary,
                pdf_filename=state.pdf_filename
            )

            elapsed = time.time() - start_time
            console.print(Panel(
                f"[cyan]向量資料庫搜索完成[/cyan]\n"
                f"處理時間: {elapsed:.2f} 秒\n"
                f"找到相關段落: {len(results)} 個",
                title="FAISS Search",
                border_style="blue"
            ))

            return {"faiss_results": results}

        except Exception as e:
            console.print(f"[red]向量資料庫搜索錯誤: {e}[/red]")
            return {"faiss_results": []}

    def _finalize_summary(self, state: SummaryState) -> Dict[str, Any]:
        """Finalize the summary with all gathered information"""
        console.print("[yellow]正在運行最終總結分支...[/yellow]")
        start_time = time.time()

        # 準備FAISS搜索結果
        faiss_content = ""
        if state.faiss_results:
            faiss_passages = [result["content"]
                              for result in state.faiss_results]
            faiss_content = "\n\n".join(faiss_passages)

        # 準備提示
        prompt = (
            f"請使用繁體中文生成最終總結報告。\n\n"
            f"研究主題：{state.research_topic}\n\n"
            f"當前總結內容：\n{state.running_summary}\n\n"
            f"向量資料庫相關內容：\n{faiss_content}\n\n"
            f"注意事項：\n"
            f"1. 必須使用繁體中文輸出\n"
            f"2. 技術術語可以附上英文原文\n"
            f"3. 保持專業和學術性的寫作風格\n"
            f"4. 確保內容的連貫性和完整性\n\n"
            f"數學公式格式規範：\n"
            f"1. 文字中的數學公式（行內公式）：\n"
            f"   - 必須且只能使用單個 $ 符號，禁止使用其他分隔符如 \\( \\) 或 \\[ \\]\n"
            f"   - 符號前後必須有空格\n"
            f"   - 正確範例：\n"
            f"     * 矩陣 $ K $ 的轉置記為 $ K^T $\n"
            f"     * 向量 $ v $ 的長度為 $ \\|v\\| $\n"
            f"     * 函數 $ f(x) $ 在點 $ x = a $ 的導數\n"
            f"   - 錯誤範例：\n"
            f"     * 矩陣\\(K\\)的轉置（使用了錯誤的分隔符）\n"
            f"     * 向量$v$的長度（分隔符前後沒有空格）\n"
            f"2. 獨立顯示的數學公式：\n"
            f"   - 必須使用雙 $$ 符號\n"
            f"   - 符號前後必須有空格\n"
            f"   - 例如：\n"
            f"     $$ \\frac{{d}}{{dx}}f(x) = \\lim_{{h \\to 0}}\\frac{{f(x+h)-f(x)}}{{h}} $$\n"
            f"3. 重要規定：\n"
            f"   - 所有數學符號和表達式都必須使用 $ 或 $$ 作為分隔符，禁止使用其他分隔符\n"
            f"   - 複雜的數學表達式也必須使用 $ 符號，例如：\n"
            f"     * 矩陣運算 $ A_{{ij}} = \\sum_{{k=1}}^n B_{{ik}}C_{{kj}} $\n"
            f"     * 概率表達式 $ P(X \\leq x) = \\int_{{-\\infty}}^x f(t)dt $"
        )

        # 使用LLM生成最終總結
        result = self.research_llm.invoke([
            SystemMessage(content=final_summarize_instructions),
            SystemMessage(content=(
                "您必須嚴格遵守以下數學公式格式規則：\n\n"
                "1. 行內數學公式的規定：\n"
                "   - 必須使用單個 $ 符號作為分隔符\n"
                "   - 嚴禁使用 \\( \\) 或其他分隔符\n"
                "   - 分隔符前後必須有空格\n"
                "   - 範例：\n"
                "     * 正確：矩陣 $ K $ 和向量 $ v $ 的乘積為 $ Kv $\n"
                "     * 正確：當 $ n \\to \\infty $ 時函數值為 $ f(x) $\n"
                "     * 錯誤：\\(K\\) 和 \\(v\\) 的乘積（使用了錯誤的分隔符）\n"
                "     * 錯誤：矩陣$K$的值（分隔符前後沒有空格）\n\n"
                "2. 獨立數學公式的規定：\n"
                "   - 必須使用雙 $$ 符號\n"
                "   - 分隔符前後必須有空格\n"
                "   - 範例：\n"
                "     $$ \\int_{{0}}^{{\\infty}} e^{{-x}} dx = 1 $$\n\n"
                "3. 數學符號使用規則：\n"
                "   - 所有數學符號必須使用 LaTeX 語法\n"
                "   - 必須使用 $ 或 $$ 作為分隔符，嚴禁使用其他分隔符\n"
                "   - 範例：\n"
                "     * 矩陣乘法：$ AB = \\sum_{{k=1}}^n a_{{ik}}b_{{kj}} $\n"
                "     * 向量內積：$ \\langle u, v \\rangle = u^T v $\n"
                "     * 概率密度：$ f(x) = \\frac{{1}}{{\\sqrt{{2\\pi}}}}e^{{-x^2/2}} $\n\n"
                "4. 語言要求：\n"
                "   - 使用繁體中文\n"
                "   - 技術術語需要時可附上英文\n"
                "   - 保持專業的學術寫作風格"
            )),
            HumanMessage(content=prompt)
        ])

        final_summary = result.content

        # 添加來源信息
        if state.sources_gathered:
            sources_text = "\n".join(state.sources_gathered)
            final_summary = f"{final_summary}\n\n### Sources:\n{sources_text}"

        result = {"running_summary": final_summary}

        elapsed = time.time() - start_time
        console.print(Panel(f"[cyan]最終總結完成[/cyan]\n處理時間: {elapsed:.2f} 秒",
                            title="Final Summary",
                            border_style="blue"))

        return result
