import json
import os
import re

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from src.models import get_planner_model
from src.prompts.planner_prompt import STRATEGIC_PLANNER_PROMPT
from src.schemas import StrategicPlan
from src.utils.logging_utils import print_node_header
from src.utils.structured_logging import (
    log_kb_status,
    log_node_execution,
    log_performance,
    log_query_allocation,
)


def check_kb_contents():
    """
    Quick check of what's in the knowledge base
    Returns metadata about KB contents to inform query allocation
    """
    try:
        # Check if KB exists
        if not os.path.exists("chroma_db"):
            return {
                "available": False,
                "total_chunks": 0,
                "document_types": [],
                "summary": "Knowledge base not found. Use web search only.",
            }

        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vectorstore = Chroma(
            collection_name="research_agent_collection",
            embedding_function=embeddings,
            persist_directory="chroma_db",
        )

        collection = vectorstore._collection
        total_docs = collection.count()

        if total_docs == 0:
            return {
                "available": False,
                "total_chunks": 0,
                "document_types": [],
                "summary": "Knowledge base is empty. Use web search only.",
            }

        # Sample some documents to understand content
        sample = collection.peek(limit=10)
        sources = set()
        if sample and "metadatas" in sample and sample["metadatas"] is not None:
            for meta in sample["metadatas"]:
                if meta and "source" in meta and isinstance(meta["source"], str):
                    # Extract filename from path
                    source = os.path.basename(meta["source"])
                    sources.add(source)

        # Create summary
        doc_list = ", ".join(list(sources)[:5])
        if len(sources) > 5:
            doc_list += f" and {len(sources) - 5} more"

        summary = (
            f"Knowledge base contains {total_docs} chunks from documents including: {doc_list}"
        )

        return {
            "available": True,
            "total_chunks": total_docs,
            "document_types": list(sources),
            "summary": summary,
        }

    except Exception as e:
        print(f"Warning: Could not check KB contents: {e}")
        return {
            "available": False,
            "total_chunks": 0,
            "document_types": [],
            "summary": "Could not access knowledge base. Use web search only.",
        }


def planner(state):
    """
    Strategic Planner - Intelligently allocates queries between RAG and web sources

    Checks KB contents and decides optimal query distribution based on:
    - What information is likely in the knowledge base
    - What needs current/external information from web
    - Query complexity and information requirements
    - Research depth level (query count limits)
    """
    print_node_header("STRATEGIC PLANNER")

    query = state["query"]
    feedback = state.get("reason", "")
    quality_feedback = state.get("quality_feedback", "")
    loop_count = state.get("loop_count", 0)
    research_depth = state.get("research_depth", "standard")

    # Combine feedback sources (evaluator reason + quality checker feedback)
    if quality_feedback:
        feedback = f"{feedback}\n\n{quality_feedback}" if feedback else quality_feedback

    # Get depth-aware query limits
    from src.config.research_depth import get_depth_config

    depth_config = get_depth_config(research_depth)

    with log_node_execution("planner", state) as logger:
        # Step 1: Check what's in the knowledge base
        logger.info("kb_check_start")

        with log_performance(logger, "kb_contents_check"):
            kb_info = check_kb_contents()

        log_kb_status(logger, kb_info)

        # Step 2: Get strategic plan from LLM
        model = get_planner_model()

        # Use structured output for reliable parsing
        structured_llm = model.with_structured_output(StrategicPlan)

        # Build depth-aware query guidance
        depth_guidance = (
            f"\n## Research Depth: {research_depth.upper()}\n"
            f"Generate {depth_config.min_queries}-{depth_config.max_queries} total queries "
            f"(RAG + Web combined).\n"
            f"Detail level: {depth_config.detail_level}\n"
        )

        prompt = (
            STRATEGIC_PLANNER_PROMPT.format(
                query=query,
                feedback=feedback,
                kb_summary=kb_info["summary"],
                kb_available=kb_info["available"],
            )
            + depth_guidance
        )

        try:
            logger.info("llm_invoke_start", has_feedback=bool(feedback))

            with log_performance(logger, "strategic_planning"):
                plan = structured_llm.invoke(prompt)

            # Log allocation results
            log_query_allocation(logger, plan.rag_queries, plan.web_queries, plan.strategy)

            # Also print for visual feedback
            print(f"\n  Strategy: {plan.strategy}")
            print(f"  RAG Queries ({len(plan.rag_queries)}): {plan.rag_queries}")
            print(f"  Web Queries ({len(plan.web_queries)}): {plan.web_queries}\n")

            return {
                "rag_queries": plan.rag_queries,
                "web_queries": plan.web_queries,
                "allocation_strategy": plan.strategy,
                "loop_count": loop_count + 1,
            }

        except Exception as e:
            logger.warning(
                "structured_output_failed", error_type=type(e).__name__, error_message=str(e)
            )
            print(f"  Warning: Structured output failed, using fallback parsing: {e}")

            # Fallback: Try manual parsing
            response = model.invoke(prompt)
            content = response.content

            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                try:
                    plan_dict = json.loads(json_match.group(0))
                    logger.info("fallback_json_parse_success")

                    return {
                        "rag_queries": plan_dict.get("rag_queries", []),
                        "web_queries": plan_dict.get("web_queries", [query]),
                        "allocation_strategy": plan_dict.get("strategy", "Fallback allocation"),
                        "loop_count": loop_count + 1,
                    }
                except json.JSONDecodeError:
                    logger.warning("fallback_json_parse_failed")

            # Final fallback: Use original query for both
            logger.info("using_ultimate_fallback", kb_available=kb_info["available"])
            print("  Using fallback: sending query to both sources")

            return {
                "rag_queries": [query] if kb_info["available"] else [],
                "web_queries": [query],
                "allocation_strategy": "Fallback: using original query for both sources",
                "loop_count": loop_count + 1,
            }
