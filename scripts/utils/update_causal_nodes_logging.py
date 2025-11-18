#!/usr/bin/env python3
"""
Update causal inference nodes to use new logging format with model info.
"""

import re
from pathlib import Path

# Nodes to update
NODES_TO_UPDATE = [
    "src/nodes/causal_checker_node.py",
    "src/nodes/issue_analyzer_node.py",
    "src/nodes/brainstormer_node.py",
    "src/nodes/evidence_planner_node.py",
    "src/nodes/hypothesis_validator_node.py",
]

# Mapping of old print statements to node names
NODE_PRINT_MAPPING = {
    'print("---CAUSAL CHECKER---")': 'print_node_header("CAUSAL CHECKER")',
    'print("---ISSUE ANALYZER---")': 'print_node_header("ISSUE ANALYZER")',
    'print("---BRAINSTORMER---")': 'print_node_header("BRAINSTORMER")',
    'print("---EVIDENCE PLANNER---")': 'print_node_header("EVIDENCE PLANNER")',
    'print("---HYPOTHESIS VALIDATOR---")': 'print_node_header("HYPOTHESIS VALIDATOR")',
}

def update_node(file_path: str):
    """Update a single node file"""
    path = Path(file_path)

    if not path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False

    # Read file
    with open(path, 'r') as f:
        content = f.read()

    original_content = content

    # Add import if not present
    if "from src.utils.logging_utils import print_node_header" not in content:
        # Find the import section (after docstring, before function definition)
        # Look for existing imports
        import_match = re.search(r'(from src\.\w+ import .+\n)', content)
        if import_match:
            # Add after last import
            last_import_pos = import_match.end()
            content = (
                content[:last_import_pos] +
                "from src.utils.logging_utils import print_node_header\n" +
                content[last_import_pos:]
            )
        else:
            # Add after docstring
            docstring_end = content.find('"""', 10)
            if docstring_end != -1:
                insert_pos = content.find('\n', docstring_end) + 1
                content = (
                    content[:insert_pos] +
                    "\nfrom src.utils.logging_utils import print_node_header\n" +
                    content[insert_pos:]
                )

    # Replace print statements
    for old_print, new_print in NODE_PRINT_MAPPING.items():
        content = content.replace(old_print, new_print)

    if content != original_content:
        # Write updated content
        with open(path, 'w') as f:
            f.write(content)
        print(f"✓ Updated: {file_path}")
        return True
    else:
        print(f"  No changes: {file_path}")
        return False

def main():
    print("Updating causal inference nodes with new logging format...\n")

    updated_count = 0
    for node_file in NODES_TO_UPDATE:
        if update_node(node_file):
            updated_count += 1

    print(f"\n✓ Updated {updated_count}/{len(NODES_TO_UPDATE)} files")
    print("\nAll causal inference nodes now show which LLM is being used!")

if __name__ == "__main__":
    main()
