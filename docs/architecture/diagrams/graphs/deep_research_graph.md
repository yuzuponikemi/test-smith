# Deep Research - Graph Visualization

**Description:** Hierarchical multi-agent research with dynamic replanning

**Version:** 2.1

**Complexity:** high

## Use Cases

- Complex multi-faceted research questions
- Topics requiring deep exploration
- Queries benefiting from subtask decomposition
- Adaptive research that discovers new angles mid-execution

## Features

- Hierarchical task decomposition
- Dynamic replanning (Phase 4)
- Depth-aware exploration
- Strategic query allocation (RAG vs Web)
- Recursive drill-down up to 2 levels
- Budget-aware execution control

## Graph Structure

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	planner(planner)
	searcher(searcher)
	rag_retriever(rag_retriever)
	analyzer(analyzer)
	evaluator(evaluator)
	synthesizer(synthesizer)
	master_planner(master_planner)
	subtask_executor(subtask_executor)
	save_result(save_result)
	depth_evaluator(depth_evaluator)
	drill_down_generator(drill_down_generator)
	plan_revisor(plan_revisor)
	__end__([<p>__end__</p>]):::last
	__start__ --> master_planner;
	analyzer -.-> depth_evaluator;
	analyzer -.-> evaluator;
	depth_evaluator --> drill_down_generator;
	drill_down_generator --> plan_revisor;
	evaluator -.-> planner;
	evaluator -.-> save_result;
	evaluator -.-> synthesizer;
	master_planner -. &nbsp;simple&nbsp; .-> planner;
	master_planner -. &nbsp;execute_subtask&nbsp; .-> subtask_executor;
	master_planner -. &nbsp;synthesize&nbsp; .-> synthesizer;
	plan_revisor --> save_result;
	planner --> rag_retriever;
	planner --> searcher;
	rag_retriever --> analyzer;
	save_result -. &nbsp;execute_subtask&nbsp; .-> subtask_executor;
	save_result -. &nbsp;synthesize&nbsp; .-> synthesizer;
	searcher --> analyzer;
	subtask_executor --> planner;
	synthesizer --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## Viewing Instructions

This diagram can be viewed in:
- GitHub (native Mermaid support)
- VS Code with Mermaid extension
- [Mermaid Live Editor](https://mermaid.live/)
- Convert to PNG: `mmdc -i deep_research_graph.md -o deep_research.png`
