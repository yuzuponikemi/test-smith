"""
Term Definer Node

Extracts technical terms/proper nouns from the query and retrieves
their definitions BEFORE main research begins. This prevents topic drift
caused by misunderstanding key terms.
"""

import logging

from src.models import get_planner_model
from src.prompts.term_definer_prompt import TERM_DEFINITION_PROMPT, TERM_EXTRACTOR_PROMPT
from src.schemas import ExtractedTerms, TermDefinition
from src.utils.logging_utils import print_node_header

logger = logging.getLogger(__name__)


def term_definer_node(state: dict) -> dict:
    """
    Extract technical terms from query and retrieve their definitions.

    This node runs BEFORE the main planning phase to ensure all key terms
    are properly understood, preventing research from going off-track.
    """
    print_node_header("TERM DEFINER")

    query = state.get("query", "")

    if not query:
        return {"term_definitions": {}, "extracted_terms": []}

    # Step 1: Extract technical terms/proper nouns from query
    print("  Step 1: Extracting technical terms from query...")
    extractor_llm = get_planner_model().with_structured_output(ExtractedTerms)

    try:
        extracted = extractor_llm.invoke(TERM_EXTRACTOR_PROMPT.format(query=query))
        terms = extracted.terms if extracted.terms else []
        print(f"  Extracted terms: {terms}")
    except Exception as e:
        logger.warning(f"Term extraction failed: {e}")
        print(f"  Warning: Term extraction failed: {e}")
        return {"term_definitions": {}, "extracted_terms": []}

    if not terms:
        print("  No technical terms found, skipping definition lookup")
        return {"term_definitions": {}, "extracted_terms": []}

    # Step 2: Look up definitions for each term via web search
    print(f"  Step 2: Looking up definitions for {len(terms)} terms...")

    term_definitions: dict[str, dict] = {}
    definition_llm = get_planner_model().with_structured_output(TermDefinition)

    # Import search tool
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        search_tool = TavilySearchResults(max_results=3)
        search_available = True
    except Exception:
        search_available = False
        print("  Warning: Web search not available for term definitions")

    for term in terms:
        print(f"    Looking up: {term}")

        # Search for definition
        search_results = []
        if search_available:
            try:
                # Search with definition-focused queries
                queries = [
                    f"{term} とは 公式",
                    f"{term} official documentation",
                    f"what is {term}",
                ]
                for q in queries[:2]:  # Limit to 2 queries per term
                    results = search_tool.invoke(q)
                    if results:
                        search_results.extend(results[:2])
            except Exception as e:
                logger.warning(f"Search failed for term '{term}': {e}")

        # Generate structured definition from search results
        search_context = (
            "\n".join(
                [f"- {r.get('content', r.get('snippet', ''))[:500]}" for r in search_results[:4]]
            )
            if search_results
            else "No search results available."
        )

        try:
            definition = definition_llm.invoke(
                TERM_DEFINITION_PROMPT.format(term=term, query=query, search_results=search_context)
            )

            term_definitions[term] = {
                "category": definition.category,
                "definition": definition.definition,
                "key_features": definition.key_features,
                "common_confusions": definition.common_confusions,
                "confidence": definition.confidence,
            }

            confidence_indicator = (
                "✓"
                if definition.confidence == "high"
                else "?"
                if definition.confidence == "medium"
                else "⚠"
            )
            print(
                f"      {confidence_indicator} {definition.category}: {definition.definition[:80]}..."
            )

        except Exception as e:
            logger.warning(f"Definition generation failed for '{term}': {e}")
            term_definitions[term] = {
                "category": "unknown",
                "definition": f"Could not determine definition for {term}",
                "key_features": [],
                "common_confusions": [],
                "confidence": "low",
            }

    # Step 3: Generate summary for downstream nodes
    print(f"  Defined {len(term_definitions)} terms")

    return {
        "term_definitions": term_definitions,
        "extracted_terms": terms,
    }


def format_term_definitions_for_prompt(term_definitions: dict) -> str:
    """
    Format term definitions for inclusion in downstream prompts.

    Returns a string that can be injected into Planner/Analyzer/Evaluator prompts
    to ensure consistent understanding of key terms.
    """
    if not term_definitions:
        return "No technical terms requiring special definition were identified."

    lines = ["## Verified Term Definitions (USE THESE AS GROUND TRUTH)\n"]

    for term, info in term_definitions.items():
        confidence = info.get("confidence", "unknown")
        confidence_marker = {"high": "✓", "medium": "?", "low": "⚠"}.get(confidence, "?")

        lines.append(f"### {term} {confidence_marker}")
        lines.append(f"**Category:** {info.get('category', 'unknown')}")
        lines.append(f"**Definition:** {info.get('definition', 'Unknown')}")

        features = info.get("key_features", [])
        if features:
            lines.append("**Key Features:**")
            for f in features[:5]:
                lines.append(f"  - {f}")

        confusions = info.get("common_confusions", [])
        if confusions:
            lines.append("**Common Confusions to Avoid:**")
            for c in confusions[:3]:
                lines.append(f"  - ❌ {c}")

        lines.append("")

    lines.append("---")
    lines.append(
        "**IMPORTANT:** If your research results contradict these definitions, flag this as a potential topic drift."
    )

    return "\n".join(lines)
