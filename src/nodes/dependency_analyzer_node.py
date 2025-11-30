"""
Dependency Analyzer Node - Analyzes code dependencies and relationships

This node analyzes retrieved code to identify:
- Import dependencies
- Class inheritance and composition
- Function call relationships
- Module dependencies
"""

import json
import re

from langchain_core.prompts import PromptTemplate

from src.models import get_analyzer_model
from src.prompts.code_investigation_prompts import DEPENDENCY_ANALYZER_PROMPT
from src.utils.logging_utils import print_node_header


def dependency_analyzer_node(state):
    """
    Dependency Analyzer Node - Analyzes dependencies between code components

    Takes retrieved code and identifies dependency relationships.
    """
    print_node_header("DEPENDENCY ANALYZER")

    query = state.get("query", "")
    target_elements = state.get("target_elements", [])
    code_results = state.get("code_results", [])

    if not code_results:
        print("  No code results to analyze")
        return {
            "dependencies": [],
            "import_analysis": [],
            "key_findings": ["No code retrieved for dependency analysis"],
            "architecture_patterns": []
        }

    # Combine code results
    code_context = "\n\n".join(code_results)

    print(f"  Analyzing dependencies in {len(code_context)} chars of code")
    print(f"  Target elements: {target_elements}")

    # Create prompt
    prompt = PromptTemplate(
        template=DEPENDENCY_ANALYZER_PROMPT,
        input_variables=["query", "target_elements", "code_context"]
    )

    # Get model
    model = get_analyzer_model()
    chain = prompt | model

    try:
        response = chain.invoke({
            "query": query,
            "target_elements": ", ".join(target_elements) if target_elements else "Not specified",
            "code_context": code_context[:15000]  # Limit context size
        })

        # Extract content
        result = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback: do basic analysis
            analysis = _analyze_dependencies_basic(code_context, target_elements)

        dependencies = analysis.get("dependencies", [])
        import_analysis = analysis.get("import_analysis", [])
        key_findings = analysis.get("key_findings", [])
        architecture_patterns = analysis.get("architecture_patterns", [])

        print(f"  Found {len(dependencies)} dependencies")
        print(f"  Found {len(import_analysis)} import groups")
        print(f"  Key findings: {len(key_findings)}")
        print(f"  Patterns: {architecture_patterns}")

        # Build dependency graph structure
        dependency_graph = _build_dependency_graph(dependencies)

        return {
            "dependencies": dependencies,
            "dependency_graph": dependency_graph,
            "import_analysis": import_analysis,
            "key_findings": key_findings,
            "architecture_patterns": architecture_patterns
        }

    except Exception as e:
        print(f"  Error analyzing dependencies: {e}")
        # Return basic analysis
        basic = _analyze_dependencies_basic(code_context, target_elements)
        return {
            "dependencies": basic.get("dependencies", []),
            "dependency_graph": {},
            "import_analysis": basic.get("import_analysis", []),
            "key_findings": [f"Basic analysis only due to error: {str(e)}"],
            "architecture_patterns": []
        }


def _analyze_dependencies_basic(code_context: str, target_elements: list) -> dict:
    """Basic dependency analysis using regex patterns"""

    dependencies = []
    import_analysis = []

    # Find Python imports
    python_imports = re.findall(
        r'^(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s]+)',
        code_context,
        re.MULTILINE
    )
    for from_module, imports in python_imports:
        import_list = [i.strip() for i in imports.split(',')]
        import_analysis.append({
            "module": from_module if from_module else "direct",
            "imports": import_list,
            "is_internal": not from_module or not from_module.startswith(('os', 'sys', 'json', 're'))
        })

    # Find C# usings
    csharp_usings = re.findall(r'^using\s+([\w.]+);', code_context, re.MULTILINE)
    for using in csharp_usings:
        import_analysis.append({
            "module": using,
            "imports": [using.split('.')[-1]],
            "is_internal": using.startswith(('MyApp', 'Internal'))
        })

    # Find class definitions and inheritance
    class_defs = re.findall(
        r'class\s+(\w+)(?:\s*\(\s*([\w,\s]+)\s*\))?:',
        code_context
    )
    for class_name, bases in class_defs:
        if bases:
            for base in bases.split(','):
                base = base.strip()
                if base and base not in ('object', 'Object'):
                    dependencies.append({
                        "source": class_name,
                        "target": base,
                        "type": "inheritance",
                        "description": f"{class_name} inherits from {base}"
                    })

    # Find C# class inheritance
    csharp_classes = re.findall(
        r'class\s+(\w+)\s*:\s*([\w,\s<>]+)',
        code_context
    )
    for class_name, bases in csharp_classes:
        for base in bases.split(','):
            base = base.strip()
            if base:
                dep_type = "implementation" if base.startswith('I') else "inheritance"
                dependencies.append({
                    "source": class_name,
                    "target": base,
                    "type": dep_type,
                    "description": f"{class_name} {'implements' if dep_type == 'implementation' else 'inherits from'} {base}"
                })

    return {
        "dependencies": dependencies,
        "import_analysis": import_analysis,
        "key_findings": [
            f"Found {len(dependencies)} class relationships",
            f"Found {len(import_analysis)} import statements"
        ],
        "architecture_patterns": []
    }


def _build_dependency_graph(dependencies: list) -> dict:
    """Build a graph structure from dependencies"""

    nodes = set()
    edges = []

    for dep in dependencies:
        source = dep.get("source", "unknown")
        target = dep.get("target", "unknown")
        nodes.add(source)
        nodes.add(target)
        edges.append({
            "from": source,
            "to": target,
            "type": dep.get("type", "unknown"),
            "label": dep.get("type", "")
        })

    return {
        "nodes": [{"id": n, "label": n} for n in nodes],
        "edges": edges
    }
