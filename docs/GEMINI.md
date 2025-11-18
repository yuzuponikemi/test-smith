# Project Overview

This project is a multi-agent research assistant that uses LangGraph to answer user queries. It leverages local language models via Ollama. The system follows a "Plan-and-Execute" strategy where a team of specialized agents collaborates to find the best possible answer to a user's query.

The primary workflow is as follows:

1.  **Planner:** Generates a set of search queries based on the user's query.
2.  **Searcher & RAG Retriever:** The search queries are executed in parallel by a web searcher (using Tavily) and a RAG retriever that searches a local vector store.
3.  **Analyzer:** Processes the search results from both sources to extract relevant information.
4.  **Evaluator:** Assesses if the gathered information is sufficient. If not, it loops back to the Planner.
5.  **Synthesizer:** Generates a comprehensive report from the analyzed data.

## Building and Running

### Prerequisites

*   Python 3.8+
*   Ollama installed and running.
*   Tavily API Key: This project uses Tavily for web searches. You need to get a free API key from [https://tavily.com/](https://tavily.com/) and set it as an environment variable:
    ```bash
    export TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    ```

### Installation

1.  Create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the application

To run the research assistant, use the `main.py` script with the `run` command, followed by your query.

```bash
python main.py run "YOUR_QUERY_HERE"
```

## Development Conventions

*   The project uses `pydantic` for data validation.
*   The agent graph is defined in `src/graph.py` using `langgraph`.
*   The different agents (nodes) are implemented as separate modules in the `src/nodes` directory.
*   Prompts for the agents are stored in the `src/prompts` directory.
*   The project uses local LLMs from Ollama, configured in `src/models.py`.
