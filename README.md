# Multi-Agent Research Assistant

This project implements a multi-agent research assistant using LangGraph, designed to answer user queries through an iterative process of planning, searching, and analysis. The system leverages local language models via Ollama and provides observability through LangSmith.

## Architecture

The research assistant employs a "Plan-and-Execute" strategy, where a team of specialized agents collaborates to find the best possible answer to a user's query. The workflow is orchestrated as a graph, with nodes representing different agents and edges representing the flow of information.

The primary workflow is as follows:

1.  **Planner:** Based on the user's query, the Planner agent generates a set of search queries to be executed.
2.  **Searcher:** The Searcher agent executes the search queries using DuckDuckGo and gathers the results.
3.  **Analyzer:** The Analyzer agent processes the search results, extracting relevant information and identifying key insights.
4.  **Evaluator:** The Evaluator agent assesses whether the gathered information is sufficient to answer the user's query.
    *   If the information is **insufficient**, the process loops back to the Planner to generate new search queries based on the current context.
    *   If the information is **sufficient**, the workflow proceeds to the Synthesizer.
5.  **Synthesizer:** The Synthesizer agent generates a comprehensive report based on all the gathered and analyzed information.

This entire process can be visualized and monitored in LangSmith, providing a clear view of each agent's actions and decisions.

## Getting Started

Follow these steps to set up and run the multi-agent research assistant.

### Prerequisites

1.  **Python 3.8+**
2.  **Ollama:** This project uses local language models served through Ollama. You must have Ollama installed and running. You can download it from [https://ollama.ai/](https://ollama.ai/).
3.  **Required Models:** Once Ollama is installed, you need to pull the required models. Open your terminal and run:
    ```bash
    ollama pull llama3
    ollama pull command-r
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

### Configuration

1.  **Set up LangSmith:** To monitor the agent's execution, you need to configure LangSmith. Create a `.env` file in the root of the project and add the following variables:

    ```
    LANGCHAIN_TRACING_V2="true"
    LANGCHAIN_API_KEY="YOUR_LANGCHAIN_API_KEY"
    LANGCHAIN_PROJECT="YOUR_LANGCHAIN_PROJECT_NAME"
    ```

    Replace `"YOUR_LANGCHAIN_API_KEY"` and `"YOUR_LANGCHAIN_PROJECT_NAME"` with your actual LangSmith API key and desired project name.

## Usage

To run the research assistant, use the `main.py` script with the `run` command, followed by your query.

### Command-Line Execution

```bash
python main.py run "YOUR_QUERY_HERE"
```

For example:

```bash
python main.py run "What are the latest advancements in AI-powered drug discovery?"
```

The agent will then begin its research process, and you will see the final report printed to the console.

### Observing in LangSmith

1.  Log in to your LangSmith account.
2.  Navigate to the project you specified in the `.env` file.
3.  You will see a trace for each execution of the research assistant.
4.  Click on a trace to view the detailed execution graph, including the inputs and outputs of each agent (node). This allows you to observe the agent's reasoning process, the search queries it generates, the results it analyzes, and its final conclusion.

## Project Structure

```
.
├───.gitignore
├───main.py                 # Main entry point for the application
├───projecttarget.md
├───README.md               # This file
├───requirements.in
├───requirements.txt        # Python dependencies
├───.venv/
└───src/
    ├───graph.py            # Defines the LangGraph agent graph and state
    ├───models.py           # Configures and provides the LLMs (via Ollama)
    ├───schemas.py          # Defines data structures for the agents
    ├───nodes/              # Contains the logic for each agent (node) in the graph
    │   ├───analyzer_node.py
    │   ├───evaluator_node.py
    │   ├───planner_node.py
    │   ├───searcher_node.py
    │   └───synthesizer_node.py
    └───prompts/            # Contains the prompt templates for each agent
        ├───analyzer_prompt.py
        ├───evaluator_prompt.py
        ├───planner_prompt.py
        └───synthesizer_prompt.py
```
