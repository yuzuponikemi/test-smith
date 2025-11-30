"""
Streaming Output Formatter for Progressive Research Results

This module provides real-time streaming output for the Test-Smith research agent,
showing progressive results as they are discovered instead of waiting for batch output.

Benefits:
- Reduces user anxiety by showing immediate progress
- Enables mid-research course correction
- Feels more interactive and collaborative
- Allows cancellation if going in wrong direction

Usage:
    from src.utils.streaming_output import StreamingFormatter

    formatter = StreamingFormatter(graph_name="deep_research")

    for chunk in app.stream(inputs, config, stream_mode="updates"):
        for node_name, value in chunk.items():
            formatter.process_node_output(node_name, value)

    formatter.finalize()
"""

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"

    # Bright versions
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"

    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output"""
        for attr in dir(cls):
            if not attr.startswith("_") and attr.isupper():
                setattr(cls, attr, "")


# Check if stdout supports colors
if not sys.stdout.isatty():
    Colors.disable()


@dataclass
class StreamingState:
    """Track streaming state across node executions"""

    # Progress tracking
    nodes_executed: list[str] = field(default_factory=list)
    total_expected_nodes: int = 10  # Will be adjusted based on graph type

    # Current phase tracking
    current_phase: str = "Initializing"
    current_subtask: Optional[str] = None
    subtask_count: int = 0
    completed_subtasks: int = 0

    # Findings accumulation
    key_findings: list[str] = field(default_factory=list)
    sources_consulted: list[str] = field(default_factory=list)

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class StreamingFormatter:
    """
    Formats and displays progressive research results in real-time.

    This class processes node outputs from LangGraph streaming and displays
    user-friendly progress updates showing:
    - Overall progress percentage
    - Current phase/activity
    - Key findings as discovered
    - Sources being consulted
    """

    # Node descriptions for user-friendly output
    NODE_DESCRIPTIONS = {
        # Planning nodes
        "master_planner": "Analyzing query complexity and creating research plan",
        "planner": "Allocating queries between knowledge base and web search",
        "subtask_executor": "Setting up subtask execution",
        # Research nodes
        "searcher": "Searching the web for information",
        "rag_retriever": "Searching internal knowledge base",
        # Analysis nodes
        "analyzer": "Analyzing and synthesizing gathered information",
        "evaluator": "Evaluating information sufficiency",
        "depth_evaluator": "Assessing research depth and quality",
        "reflection": "Performing meta-reasoning critique",
        # Generation nodes
        "drill_down_generator": "Generating follow-up research questions",
        "plan_revisor": "Adapting research plan based on discoveries",
        "save_result": "Saving subtask results",
        "synthesizer": "Generating final comprehensive report",
        # Causal inference nodes
        "issue_analyzer": "Analyzing issue symptoms and context",
        "brainstormer": "Generating root cause hypotheses",
        "evidence_planner": "Planning evidence gathering strategy",
        "causal_checker": "Validating causal relationships",
        "hypothesis_validator": "Ranking hypotheses by likelihood",
        "causal_graph_builder": "Building causal relationship graph",
        "root_cause_synthesizer": "Generating root cause analysis report",
        # Fact check nodes
        "claim_extractor": "Extracting claims to verify",
        "evidence_gatherer": "Gathering evidence for claims",
        "verdict_generator": "Generating fact-check verdicts",
        # Comparative nodes
        "comparison_planner": "Planning comparison analysis",
        "comparison_synthesizer": "Generating comparison report",
    }

    # Expected node counts by graph type
    EXPECTED_NODES = {
        "deep_research": 15,
        "quick_research": 7,
        "fact_check": 8,
        "comparative": 10,
        "causal_inference": 12,
    }

    def __init__(self, graph_name: str = "deep_research", use_colors: bool = True):
        """
        Initialize the streaming formatter.

        Args:
            graph_name: Name of the graph being executed
            use_colors: Whether to use ANSI colors in output
        """
        self.graph_name = graph_name
        self.state = StreamingState()
        self.state.total_expected_nodes = self.EXPECTED_NODES.get(graph_name, 10)

        if not use_colors:
            Colors.disable()

        # Print initial header
        self._print_header()

    def _print_header(self):
        """Print the streaming output header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}")
        print(
            f"{Colors.BOLD}{Colors.CYAN}  Test-Smith Research Agent - Live Progress{Colors.RESET}"
        )
        print(f"{Colors.CYAN}{'═' * 70}{Colors.RESET}\n")

    def _get_progress_bar(self, percentage: float, width: int = 30) -> str:
        """Generate a visual progress bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        bar = f"{'█' * filled}{'░' * empty}"
        return f"[{bar}] {percentage:.0f}%"

    def _calculate_progress(self) -> float:
        """Calculate overall progress percentage"""
        if self.state.total_expected_nodes == 0:
            return 0

        # Weight progress based on node importance
        base_progress = (len(self.state.nodes_executed) / self.state.total_expected_nodes) * 100

        # Cap at 95% until synthesizer completes
        if (
            "synthesizer" not in self.state.nodes_executed
            and "root_cause_synthesizer" not in self.state.nodes_executed
        ):
            base_progress = min(base_progress, 95)

        return min(base_progress, 100)

    def _extract_key_findings(self, node_name: str, value: dict[str, Any]) -> list[str]:
        """Extract key findings from node output"""
        findings = []

        # Extract from analyzed_data
        if "analyzed_data" in value:
            data = value["analyzed_data"]
            if isinstance(data, list) and data:
                # Get the latest analysis (last item)
                latest = data[-1] if data else ""
                if isinstance(latest, str) and len(latest) > 50:
                    # Extract first meaningful sentence
                    sentences = re.split(r"[.!?]+", latest)
                    for sentence in sentences[:2]:
                        sentence = sentence.strip()
                        if len(sentence) > 30 and len(sentence) < 200:
                            findings.append(sentence)
                            break

        # Extract from search results
        if node_name == "searcher" and "search_results" in value:
            results = value.get("search_results", [])
            if results:
                findings.append(f"Found {len(results)} web results")

        # Extract from RAG results
        if node_name == "rag_retriever" and "rag_results" in value:
            results = value.get("rag_results", [])
            if results:
                findings.append(f"Retrieved {len(results)} knowledge base chunks")

        # Extract from evaluation
        if "evaluation" in value:
            eval_text = value["evaluation"]
            if "sufficient" in eval_text.lower():
                findings.append("Information sufficiency: adequate")
            elif "insufficient" in eval_text.lower():
                findings.append("Need more information, refining search")

        # Extract from master plan
        if node_name == "master_planner" and "master_plan" in value:
            plan = value.get("master_plan", {})
            if plan:
                subtasks = plan.get("subtasks", [])
                self.state.subtask_count = len(subtasks)
                if plan.get("is_complex"):
                    findings.append(f"Complex query: decomposed into {len(subtasks)} subtasks")
                else:
                    findings.append("Simple query: using direct research approach")

        # Extract hypothesis count for causal inference
        if node_name == "brainstormer" and "hypotheses" in value:
            hypotheses = value.get("hypotheses", [])
            findings.append(f"Generated {len(hypotheses)} root cause hypotheses")

        return findings

    def _extract_sources(self, _node_name: str, value: dict[str, Any]) -> list[str]:
        """Extract source information from node output"""
        sources = []

        # From search results
        if "search_results" in value:
            results = value.get("search_results", [])
            for result in results:
                if isinstance(result, str):
                    # Try to extract URLs
                    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', result)
                    for url in urls[:2]:  # Limit to 2 URLs per result
                        # Clean and shorten URL for display
                        domain = re.search(r"https?://([^/]+)", url)
                        if domain:
                            sources.append(domain.group(1))

        return list(set(sources))  # Remove duplicates

    def _update_phase(self, node_name: str, value: dict[str, Any]):
        """Update current phase based on node execution"""

        # Map nodes to phases
        phase_map = {
            "master_planner": "Planning Research Strategy",
            "planner": "Allocating Queries",
            "subtask_executor": "Executing Subtask",
            "searcher": "Web Search",
            "rag_retriever": "Knowledge Base Search",
            "analyzer": "Analyzing Results",
            "evaluator": "Evaluating Quality",
            "depth_evaluator": "Evaluating Depth",
            "reflection": "Meta-Reasoning Critique",
            "drill_down_generator": "Generating Follow-ups",
            "plan_revisor": "Revising Plan",
            "save_result": "Saving Results",
            "synthesizer": "Generating Report",
            "issue_analyzer": "Analyzing Issue",
            "brainstormer": "Brainstorming Causes",
            "evidence_planner": "Planning Evidence Gathering",
            "causal_checker": "Checking Causality",
            "hypothesis_validator": "Validating Hypotheses",
            "causal_graph_builder": "Building Causal Graph",
            "root_cause_synthesizer": "Generating RCA Report",
        }

        self.state.current_phase = phase_map.get(node_name, self.state.current_phase)

        # Track subtask
        if "current_subtask_id" in value:
            subtask_id = value["current_subtask_id"]
            if subtask_id != self.state.current_subtask:
                if self.state.current_subtask:
                    self.state.completed_subtasks += 1
                self.state.current_subtask = subtask_id

    def process_node_output(self, node_name: str, value: dict[str, Any]):
        """
        Process output from a node and display progressive update.

        Args:
            node_name: Name of the node that produced this output
            value: The output dictionary from the node
        """
        # Track node execution
        if node_name not in self.state.nodes_executed:
            self.state.nodes_executed.append(node_name)

        # Update timing
        self.state.last_update = datetime.now()

        # Update phase
        self._update_phase(node_name, value)

        # Extract findings and sources
        new_findings = self._extract_key_findings(node_name, value)
        new_sources = self._extract_sources(node_name, value)

        # Add to state
        self.state.key_findings.extend(new_findings)
        self.state.sources_consulted.extend(new_sources)

        # Display update
        self._display_update(node_name, new_findings, new_sources)

    def _display_update(self, node_name: str, new_findings: list[str], new_sources: list[str]):
        """Display a streaming update to the user"""

        # Calculate progress
        progress = self._calculate_progress()
        progress_bar = self._get_progress_bar(progress)

        # Get node description
        description = self.NODE_DESCRIPTIONS.get(node_name, f"Processing {node_name}")

        # Build output
        elapsed = (datetime.now() - self.state.start_time).total_seconds()

        # Progress line
        print(f"\r{Colors.BOLD}{Colors.GREEN}{progress_bar}{Colors.RESET}", end="")
        print(f"  {Colors.DIM}[{elapsed:.1f}s]{Colors.RESET}")

        # Current activity
        phase_indicator = f"{Colors.BRIGHT_CYAN}▸{Colors.RESET}"
        print(f"{phase_indicator} {Colors.BOLD}{self.state.current_phase}{Colors.RESET}")
        print(f"  {Colors.DIM}{description}{Colors.RESET}")

        # Subtask info (if hierarchical)
        if self.state.subtask_count > 0 and self.state.current_subtask:
            subtask_progress = f"{self.state.completed_subtasks + 1}/{self.state.subtask_count}"
            print(
                f"  {Colors.YELLOW}Subtask: {self.state.current_subtask} ({subtask_progress}){Colors.RESET}"
            )

        # New findings
        if new_findings:
            print(f"\n  {Colors.BRIGHT_GREEN}✓ Discoveries:{Colors.RESET}")
            for finding in new_findings[-3:]:  # Show last 3 findings
                # Truncate long findings
                if len(finding) > 100:
                    finding = finding[:97] + "..."
                print(f"    {Colors.GREEN}• {finding}{Colors.RESET}")

        # New sources
        if new_sources:
            print(f"\n  {Colors.BRIGHT_BLUE}📚 Sources:{Colors.RESET}")
            for source in new_sources[-5:]:  # Show last 5 sources
                print(f"    {Colors.BLUE}• {source}{Colors.RESET}")

        # Separator
        print(f"\n{Colors.DIM}{'─' * 70}{Colors.RESET}\n")

    def finalize(self):
        """Display final summary after completion"""

        elapsed = (datetime.now() - self.state.start_time).total_seconds()

        print(f"\n{Colors.BOLD}{Colors.GREEN}{'═' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}  Research Complete!{Colors.RESET}")
        print(f"{Colors.GREEN}{'═' * 70}{Colors.RESET}\n")

        # Summary stats
        print(f"{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  • Time elapsed: {elapsed:.1f} seconds")
        print(f"  • Nodes executed: {len(self.state.nodes_executed)}")
        print(f"  • Key findings: {len(self.state.key_findings)}")
        print(f"  • Sources consulted: {len(set(self.state.sources_consulted))}")

        if self.state.subtask_count > 0:
            print(
                f"  • Subtasks completed: {self.state.completed_subtasks + 1}/{self.state.subtask_count}"
            )

        print()

    def get_state(self) -> StreamingState:
        """Get current streaming state for external inspection"""
        return self.state


def create_streaming_callback(formatter: StreamingFormatter):
    """
    Create a callback function for use with LangGraph streaming.

    Usage:
        formatter = StreamingFormatter("deep_research")
        callback = create_streaming_callback(formatter)

        for chunk in app.stream(inputs, config):
            callback(chunk)

        formatter.finalize()
    """

    def callback(chunk: dict[str, Any]):
        for node_name, value in chunk.items():
            formatter.process_node_output(node_name, value)

    return callback
