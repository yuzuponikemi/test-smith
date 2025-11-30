"""
Code Query Analyzer Node - Analyzes investigation queries to determine scope and targets

This node parses the user's question about code and determines:
- What type of investigation is needed
- What code elements to search for
- What patterns to look for
- The appropriate scope of investigation
"""

import json
import re

from langchain_core.prompts import PromptTemplate

from src.models import get_planner_model
from src.prompts.code_investigation_prompts import CODE_QUERY_ANALYZER_PROMPT
from src.utils.logging_utils import print_node_header


def code_query_analyzer_node(state):
    """
    Code Query Analyzer Node - Determines what to investigate in the codebase

    Analyzes the user's question and returns structured investigation parameters.
    """
    print_node_header("CODE QUERY ANALYZER")

    query = state.get("query", "")

    print(f"  Analyzing query: {query[:100]}...")

    # Create prompt
    prompt = PromptTemplate(template=CODE_QUERY_ANALYZER_PROMPT, input_variables=["query"])

    # Get model
    model = get_planner_model()
    chain = prompt | model

    try:
        response = chain.invoke({"query": query})

        # Extract content
        result = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from response
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback: create basic analysis
            analysis = _create_fallback_analysis(query)

        # Extract fields
        investigation_type = analysis.get("investigation_type", "general")
        target_elements = analysis.get("target_elements", [])
        search_patterns = analysis.get("search_patterns", [])
        code_queries = analysis.get("code_queries", [query])
        investigation_scope = analysis.get("investigation_scope", "medium")

        print(f"  Investigation type: {investigation_type}")
        print(f"  Target elements: {target_elements}")
        print(f"  Search patterns: {len(search_patterns)}")
        print(f"  Code queries: {len(code_queries)}")
        print(f"  Scope: {investigation_scope}")

        return {
            "investigation_type": investigation_type,
            "target_elements": target_elements,
            "search_patterns": search_patterns,
            "code_queries": code_queries,
            "investigation_scope": investigation_scope,
            "loop_count": 0,
        }

    except Exception as e:
        print(f"  Error analyzing query: {e}")
        # Return fallback analysis
        fallback = _create_fallback_analysis(query)
        return {
            "investigation_type": fallback["investigation_type"],
            "target_elements": fallback["target_elements"],
            "search_patterns": fallback["search_patterns"],
            "code_queries": fallback["code_queries"],
            "investigation_scope": fallback["investigation_scope"],
            "loop_count": 0,
        }


def _create_fallback_analysis(query: str) -> dict:
    """Create a basic analysis when LLM parsing fails"""

    # Extract potential code identifiers
    identifiers = []

    # CamelCase
    identifiers.extend(re.findall(r"\b([A-Z][a-zA-Z0-9]+)\b", query))

    # snake_case
    identifiers.extend(re.findall(r"\b([a-z_][a-z_0-9]*(?:_[a-z_0-9]+)+)\b", query.lower()))

    # Quoted terms
    identifiers.extend(re.findall(r'"([^"]+)"', query))
    identifiers.extend(re.findall(r"'([^']+)'", query))

    # Remove duplicates
    identifiers = list(set(identifiers))

    # Determine investigation type from keywords
    query_lower = query.lower()
    if any(word in query_lower for word in ["depend", "import", "use", "call"]):
        inv_type = "dependency"
    elif any(word in query_lower for word in ["flow", "pass", "data", "variable"]):
        inv_type = "flow"
    elif any(word in query_lower for word in ["where", "find", "locate", "usage"]):
        inv_type = "usage"
    elif any(word in query_lower for word in ["architecture", "structure", "pattern", "design"]):
        inv_type = "architecture"
    elif any(word in query_lower for word in ["how", "work", "implement"]):
        inv_type = "implementation"
    else:
        inv_type = "general"

    return {
        "investigation_type": inv_type,
        "target_elements": identifiers[:5],
        "search_patterns": identifiers[:3],
        "code_queries": [query] + identifiers[:4],
        "investigation_scope": "medium",
    }
