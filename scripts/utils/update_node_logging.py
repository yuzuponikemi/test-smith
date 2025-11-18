"""
Quick script to add model info to all node print statements
"""

import re
from pathlib import Path

nodes_to_update = [
    ("src/nodes/synthesizer_node.py", "SYNTHESIZER"),
    ("src/nodes/evaluator_node.py", "EVALUATOR"),
    ("src/nodes/analyzer_node.py", "ANALYZER"),
    ("src/nodes/searcher_node.py", "SEARCHER"),
    ("src/nodes/rag_retriever_node.py", "RAG RETRIEVER"),
    ("src/nodes/subtask_router.py", "SUBTASK ROUTER"),
    ("src/nodes/subtask_executor.py", "SUBTASK EXECUTOR"),
    ("src/nodes/depth_evaluator_node.py", "DEPTH EVALUATOR"),
    ("src/nodes/drill_down_generator.py", "DRILL-DOWN GENERATOR"),
    ("src/nodes/plan_revisor_node.py", "PLAN REVISOR"),
]

for filepath, node_name in nodes_to_update:
    path = Path(filepath)
    if not path.exists():
        print(f"Skipping {filepath} - not found")
        continue

    content = path.read_text()

    # Check if already has print_node_header import
    if "from src.utils.logging_utils import print_node_header" in content:
        print(f"✓ {filepath} - already updated")
        continue

    # Add import after other imports
    if "from src.models import" in content or "from src.prompts import" in content:
        # Add import after first from src. import
        content = re.sub(
            r'(from src\.\w+ import [^\n]+\n)',
            r'\1from src.utils.logging_utils import print_node_header\n',
            content,
            count=1
        )
    else:
        # Add at top after any existing imports
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                if not line.startswith('import') and not line.startswith('from'):
                    insert_idx = i
                    break
        lines.insert(insert_idx, 'from src.utils.logging_utils import print_node_header')
        content = '\n'.join(lines)

    # Replace print("---NODE NAME---") with print_node_header("NODE NAME")
    old_pattern = f'print\\("---{node_name}---"\\)'
    new_pattern = f'print_node_header("{node_name}")'

    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        path.write_text(content)
        print(f"✅ Updated {filepath}")
    else:
        print(f"⚠️  {filepath} - pattern not found")

print("\nDone!")
