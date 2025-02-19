from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from tqdm.auto import tqdm
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import time
from datetime import datetime
import os
import sys


class PDFEmbedder:
    """
    A class for embedding PDF documents into FAISS vector stores using Ollama embeddings.

    This class handles the entire process of:
    - Loading PDF documents
    - Splitting text into chunks
    - Creating embeddings
    - Saving to FAISS index
    """

    def __init__(self, model_name="mxbai-embed-large", chunk_size=1000, chunk_overlap=200):
        """
        Initialize the PDFEmbedder.

        Args:
            model_name (str): Name of the Ollama model to use for embeddings
            chunk_size (int): Size of text chunks for splitting
            chunk_overlap (int): Overlap between text chunks
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.console = Console()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs("Files", exist_ok=True)
        os.makedirs("FAISS_index", exist_ok=True)

    def _format_time(self, seconds):
        """Format time in a human readable way"""
        if seconds < 60:
            return f"{seconds:.2f} seconds"
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes} minutes {seconds:.2f} seconds"

    def _check_existing_index(self, pdf_name):
        """Check if FAISS index already exists for the given PDF"""
        base_name = os.path.splitext(pdf_name)[0]
        index_path = os.path.join("FAISS_index", base_name)
        return os.path.exists(index_path)

    def create_embeddings(self, pdf_path, force=False):
        """
        Create embeddings for a PDF document and save them to a FAISS index.

        Args:
            pdf_path (str): Path to the PDF file
            force (bool): If True, recreate embeddings even if they already exist

        Returns:
            dict: A dictionary containing timing information for each step

        Raises:
            FileNotFoundError: If the PDF file does not exist
        """
        pdf_name = os.path.basename(pdf_path)

        # Check if index already exists
        if not force and self._check_existing_index(pdf_name):
            self.console.print(f"[green]FAISS index for '{
                               pdf_name}' already exists.[/green]")
            return None

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file '{pdf_path}' not found")

        timings = {}
        total_start_time = time.time()

        # Load PDF
        pdf_start_time = time.time()
        self.console.print(Panel("[blue]Loading PDF document...[/blue]"))
        loader = PyMuPDFLoader(pdf_path)
        data = loader.load()
        timings['pdf_loading'] = time.time() - pdf_start_time
        self.console.print(f"[green]✓[/green] Loaded {len(data)} pages in [yellow]{
                           self._format_time(timings['pdf_loading'])}[/yellow]")

        # Split documents
        split_start_time = time.time()
        self.console.print(
            Panel("[blue]Splitting documents into chunks...[/blue]"))
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        texts = text_splitter.split_documents(data)
        timings['text_splitting'] = time.time() - split_start_time
        self.console.print(f"[green]✓[/green] Created {len(texts)} text chunks in [yellow]{
                           self._format_time(timings['text_splitting'])}[/yellow]")

        # Initialize Ollama embedding model
        init_start_time = time.time()
        self.console.print(
            Panel("[blue]Initializing embedding model...[/blue]"))
        embeddings = OllamaEmbeddings(model=self.model_name)
        timings['model_init'] = time.time() - init_start_time
        self.console.print(f"[green]✓[/green] Model initialized in [yellow]{
                           self._format_time(timings['model_init'])}[/yellow]")

        # Create FAISS vector store with progress bar
        embed_start_time = time.time()
        self.console.print(
            Panel("[blue]Creating FAISS vector store...[/blue]"))
        texts_with_progress = tqdm(
            texts, desc="Embedding documents", unit="chunk")
        embedded_texts = []
        chunk_times = []

        for doc in texts_with_progress:
            chunk_start = time.time()
            vector = embeddings.embed_documents([doc.page_content])
            embedded_texts.append((doc.page_content, vector[0]))
            chunk_time = time.time() - chunk_start
            chunk_times.append(chunk_time)
            texts_with_progress.set_postfix(
                {"Last chunk": f"{chunk_time:.2f}s"})

        db = FAISS.from_embeddings(
            text_embeddings=embedded_texts,
            embedding=embeddings
        )

        timings['embedding'] = time.time() - embed_start_time
        timings['avg_chunk_time'] = sum(chunk_times) / len(chunk_times)
        self.console.print(f"[green]✓[/green] Embedding completed in [yellow]{
                           self._format_time(timings['embedding'])}[/yellow]")
        self.console.print(f"[dim]Average time per chunk: {
                           self._format_time(timings['avg_chunk_time'])}[/dim]")

        # Save the vector store locally
        save_start_time = time.time()
        self.console.print(Panel("[blue]Saving vector store...[/blue]"))
        base_name = os.path.splitext(pdf_name)[0]
        save_path = os.path.join("FAISS_index", base_name)
        db.save_local(save_path)
        timings['saving'] = time.time() - save_start_time
        self.console.print(f"[green]✓[/green] Successfully saved FAISS index in [yellow]{
                           self._format_time(timings['saving'])}[/yellow]")

        # Calculate total time
        timings['total'] = time.time() - total_start_time

        # Display summary table
        self.display_summary(timings)

        return timings

    def display_summary(self, timings):
        """Display a summary table of processing times"""
        table = Table(title="Processing Time Summary")
        table.add_column("Step", style="cyan")
        table.add_column("Time", style="yellow")
        table.add_column("Percentage", style="green")

        total_time = timings['total']

        steps = [
            ("PDF Loading", 'pdf_loading'),
            ("Text Splitting", 'text_splitting'),
            ("Model Initialization", 'model_init'),
            ("Embedding", 'embedding'),
            ("Saving Index", 'saving'),
            ("Total Process", 'total')
        ]

        for step_name, timing_key in steps:
            time_value = timings[timing_key]
            percentage = (time_value/total_time) * \
                100 if timing_key != 'total' else 100
            table.add_row(
                step_name,
                self._format_time(time_value),
                f"{percentage:.1f}%"
            )

        self.console.print("\n[bold]Time Analysis Summary[/bold]")
        self.console.print(table)
        self.console.print(f"\n[dim]Process completed at: {
                           datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
