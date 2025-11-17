"""
Evidence Planner Node - Plans strategic queries for evidence gathering.

Part of the Causal Inference Graph workflow for root cause analysis.
Reuses the strategic planning approach from the research graph.
"""

import os
from pathlib import Path
from src.models import get_evidence_planner_model
from src.prompts.evidence_planner_prompt import EVIDENCE_PLANNER_PROMPT
from src.schemas import StrategicPlan


def check_kb_contents() -> str:
    """
    Check knowledge base contents and return summary.

    Returns:
        String describing KB status and contents
    """
    chroma_db_path = Path("chroma_db")

    if not chroma_db_path.exists():
        return "Knowledge Base: Not available (chroma_db/ not found)"

    try:
        # Try to get basic info about KB
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings

        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vectorstore = Chroma(
            persist_directory=str(chroma_db_path),
            embedding_function=embeddings,
            collection_name="research_agent_collection"
        )

        # Get collection stats
        collection = vectorstore._collection
        count = collection.count()

        # Sample a few documents to understand content
        if count > 0:
            sample = collection.peek(limit=3)
            sample_docs = sample.get('documents', [])[:3]
            sample_preview = " | ".join([doc[:100] for doc in sample_docs])

            return f"""Knowledge Base: Available
Total documents: {count} chunks
Sample content: {sample_preview}
Recommendation: Use for domain-specific, internal documentation, and established patterns"""
        else:
            return "Knowledge Base: Empty (no documents)"

    except Exception as e:
        return f"Knowledge Base: Error accessing ({str(e)[:100]})"


def evidence_planner_node(state: dict) -> dict:
    """
    Plans strategic queries for evidence gathering from RAG and web sources.

    Args:
        state: Current graph state with query and hypotheses

    Returns:
        Updated state with rag_queries, web_queries, and allocation_strategy
    """
    print("---EVIDENCE PLANNER---")

    query = state.get("query", "")
    issue_summary = state.get("issue_summary", "")
    hypotheses = state.get("hypotheses", [])

    print(f"  Planning evidence gathering for {len(hypotheses)} hypotheses...")

    # Check KB status
    kb_info = check_kb_contents()
    print(f"  {kb_info.split(chr(10))[0]}")  # Print first line

    # Get model with structured output
    model = get_evidence_planner_model()
    structured_model = model.with_structured_output(StrategicPlan)

    # Format hypotheses for prompt
    hypotheses_str = "\n".join([
        f"- {h['hypothesis_id']}: {h['description']}"
        for h in hypotheses
    ])

    # Format prompt and invoke
    prompt = EVIDENCE_PLANNER_PROMPT.format(
        query=query,
        issue_summary=issue_summary,
        hypotheses=hypotheses_str,
        kb_info=kb_info
    )

    plan: StrategicPlan = structured_model.invoke(prompt)

    print(f"  Planned {len(plan.rag_queries)} RAG queries, {len(plan.web_queries)} web queries")
    print(f"  Strategy: {plan.strategy[:100]}...")

    # Increment loop counter
    loop_count = state.get("loop_count", 0) + 1

    return {
        "rag_queries": plan.rag_queries,
        "web_queries": plan.web_queries,
        "allocation_strategy": plan.strategy,
        "loop_count": loop_count,
    }
