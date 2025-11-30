"""
Code Investigation Synthesizer Node - Generates comprehensive investigation reports

This node synthesizes all analysis results into a comprehensive report:
- Dependencies and relationships
- Data and control flow
- Code references with file paths
- Recommendations and insights
"""

from langchain_core.prompts import PromptTemplate

from src.models import get_synthesizer_model
from src.prompts.code_investigation_prompts import CODE_INVESTIGATION_SYNTHESIZER_PROMPT
from src.utils.logging_utils import print_node_header


def code_investigation_synthesizer_node(state):
    """
    Code Investigation Synthesizer Node - Creates comprehensive investigation report

    Synthesizes all collected analysis into a final report.
    """
    print_node_header("CODE INVESTIGATION SYNTHESIZER")

    query = state.get("query", "")
    investigation_type = state.get("investigation_type", "general")
    target_elements = state.get("target_elements", [])
    code_results = state.get("code_results", [])
    dependencies = state.get("dependencies", [])
    import_analysis = state.get("import_analysis", [])
    data_flow = state.get("data_flow", [])
    control_flow = state.get("control_flow", [])
    variable_usage = state.get("variable_usage", [])
    function_calls = state.get("function_calls", [])
    key_findings = state.get("key_findings", [])
    architecture_patterns = state.get("architecture_patterns", [])
    related_files = state.get("related_files", [])

    print(f"  Investigation type: {investigation_type}")
    print(f"  Target elements: {len(target_elements)}")
    print(f"  Code results: {len(code_results)}")
    print(f"  Dependencies: {len(dependencies)}")
    print(f"  Key findings: {len(key_findings)}")

    # Format dependency analysis
    dependency_analysis = _format_dependency_analysis(
        dependencies, import_analysis, architecture_patterns
    )

    # Format flow analysis
    flow_analysis = _format_flow_analysis(data_flow, control_flow, variable_usage, function_calls)

    # Combine code results
    code_context = "\n\n".join(code_results) if code_results else "No code retrieved"

    # Format key findings
    findings_str = (
        "\n".join(f"- {f}" for f in key_findings) if key_findings else "No specific findings"
    )

    # Create prompt
    prompt = PromptTemplate(
        template=CODE_INVESTIGATION_SYNTHESIZER_PROMPT,
        input_variables=[
            "query",
            "investigation_type",
            "target_elements",
            "code_context",
            "dependency_analysis",
            "flow_analysis",
            "key_findings",
        ],
    )

    # Get model
    model = get_synthesizer_model()
    chain = prompt | model

    try:
        response = chain.invoke(
            {
                "query": query,
                "investigation_type": investigation_type,
                "target_elements": ", ".join(target_elements)
                if target_elements
                else "Not specified",
                "code_context": code_context[:12000],  # Limit size
                "dependency_analysis": dependency_analysis,
                "flow_analysis": flow_analysis,
                "key_findings": findings_str,
            }
        )

        # Extract content
        report = response.content if hasattr(response, "content") else str(response)

        print(f"  Generated report ({len(report)} chars)")

        # Add footer with related files
        if related_files:
            report += "\n\n### Related Files\n"
            for f in related_files[:10]:
                report += f"- `{f}`\n"

        return {"report": report}

    except Exception as e:
        print(f"  Error generating report: {e}")
        # Generate basic report
        report = _generate_basic_report(
            query, investigation_type, target_elements, dependencies, key_findings, related_files
        )
        return {"report": report}


def _format_dependency_analysis(dependencies: list, imports: list, patterns: list) -> str:
    """Format dependency analysis for the prompt"""

    sections = []

    if dependencies:
        sections.append("**Dependencies:**")
        for dep in dependencies[:15]:
            source = dep.get("source", "unknown")
            target = dep.get("target", "unknown")
            dep_type = dep.get("type", "unknown")
            sections.append(f"- {source} → {target} ({dep_type})")

    if imports:
        sections.append("\n**Imports:**")
        for imp in imports[:10]:
            module = imp.get("module", "unknown")
            items = imp.get("imports", [])
            is_internal = imp.get("is_internal", False)
            marker = "[internal]" if is_internal else "[external]"
            sections.append(f"- {module}: {', '.join(items[:5])} {marker}")

    if patterns:
        sections.append("\n**Architecture Patterns:**")
        for pattern in patterns:
            sections.append(f"- {pattern}")

    return "\n".join(sections) if sections else "No dependency analysis available"


def _format_flow_analysis(
    data_flow: list, control_flow: list, variable_usage: list, function_calls: list
) -> str:
    """Format flow analysis for the prompt"""

    sections = []

    if data_flow:
        sections.append("**Data Flow:**")
        for flow in data_flow[:10]:
            var = flow.get("variable", "unknown")
            source = flow.get("source", "unknown")
            dest = flow.get("destination", "unknown")
            sections.append(f"- {var}: {source} → {dest}")

    if control_flow:
        sections.append("\n**Control Flow:**")
        for flow in control_flow[:10]:
            entry = flow.get("entry_point", "unknown")
            exits = flow.get("exit_points", [])
            sections.append(f"- {entry}: exits via {', '.join(exits)}")

    if function_calls:
        sections.append("\n**Function Calls:**")
        for call in function_calls[:15]:
            caller = call.get("caller", "unknown")
            callee = call.get("callee", "unknown")
            if caller != "unknown":
                sections.append(f"- {caller} → {callee}")
            else:
                sections.append(f"- {callee}()")

    if variable_usage:
        sections.append("\n**Key Variables:**")
        for var in variable_usage[:10]:
            name = var.get("name", "unknown")
            defined = var.get("defined_in", "unknown")
            sections.append(f"- {name}: defined in {defined}")

    return "\n".join(sections) if sections else "No flow analysis available"


def _generate_basic_report(
    query: str,
    investigation_type: str,
    target_elements: list,
    dependencies: list,
    key_findings: list,
    related_files: list,
) -> str:
    """Generate a basic report when LLM fails"""

    report = f"""## Code Investigation Report

### Query
{query}

### Investigation Type
{investigation_type}

### Target Elements
{", ".join(target_elements) if target_elements else "Not specified"}

### Dependencies Found
"""

    if dependencies:
        for dep in dependencies[:10]:
            report += f"- {dep.get('source')} → {dep.get('target')} ({dep.get('type')})\n"
    else:
        report += "No dependencies identified\n"

    report += "\n### Key Findings\n"
    if key_findings:
        for finding in key_findings:
            report += f"- {finding}\n"
    else:
        report += "No specific findings\n"

    if related_files:
        report += "\n### Related Files\n"
        for f in related_files[:10]:
            report += f"- `{f}`\n"

    report += "\n### Note\nThis is a basic report generated due to an analysis error. "
    report += "Please try running the investigation again or check the logs for details."

    return report
