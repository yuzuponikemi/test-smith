#!/usr/bin/env python3
"""
Causal Graph Visualization Script

This script generates a visual representation of the causal graph data
produced by the causal_inference workflow.

Usage:
    python visualize_causal_graph.py <causal_graph_data.json>

The script will create an HTML file with an interactive graph visualization.
"""

import json
import sys
from pathlib import Path


def generate_html_visualization(graph_data: dict, output_path: str = "causal_graph.html"):
    """
    Generate an HTML visualization using vis.js network library.

    Args:
        graph_data: Dictionary containing nodes and edges
        output_path: Path to save the HTML file
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    metadata = graph_data.get("metadata", {})

    # Convert nodes to vis.js format
    vis_nodes = []
    for node in nodes:
        node_id = node["id"]
        label = node["label"]
        node_type = node["type"]

        # Color coding by type and likelihood
        if node_type == "symptom":
            color = "#ff6b6b"  # Red for symptoms
            shape = "box"
        else:  # hypothesis
            likelihood = node.get("likelihood", 0.5)
            # Color gradient from gray (low) to green (high)
            if likelihood > 0.7:
                color = "#51cf66"  # Green - high likelihood
            elif likelihood > 0.4:
                color = "#ffd43b"  # Yellow - medium likelihood
            else:
                color = "#adb5bd"  # Gray - low likelihood
            shape = "ellipse"

        vis_nodes.append({
            "id": node_id,
            "label": label,
            "color": color,
            "shape": shape,
            "title": node.get("full_text", label)  # Tooltip with full text
        })

    # Convert edges to vis.js format
    vis_edges = []
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        strength = edge.get("strength", 0.5)
        rel_type = edge.get("relationship_type", "unknown")

        # Width based on strength
        width = max(1, strength * 5)

        # Color based on relationship type
        if rel_type == "direct_cause":
            color = "#339af0"  # Blue
        elif rel_type == "contributing_factor":
            color = "#74c0fc"  # Light blue
        elif rel_type == "correlated":
            color = "#adb5bd"  # Gray
        else:
            color = "#dee2e6"  # Light gray

        vis_edges.append({
            "from": source,
            "to": target,
            "width": width,
            "color": color,
            "title": f"{rel_type} (strength: {strength:.2f})",
            "arrows": "to"
        })

    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Causal Inference Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        #mynetwork {{
            width: 100%;
            height: 600px;
            border: 1px solid lightgray;
        }}
        .info {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1>Causal Inference Graph Visualization</h1>

    <div class="info">
        <h3>Graph Metadata</h3>
        <p><strong>Total Hypotheses:</strong> {metadata.get('total_hypotheses', 'N/A')}</p>
        <p><strong>Total Symptoms:</strong> {metadata.get('total_symptoms', 'N/A')}</p>
        <p><strong>Total Relationships:</strong> {metadata.get('total_relationships', 'N/A')}</p>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #ff6b6b;"></div>
            <span>Symptom</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #51cf66;"></div>
            <span>High Likelihood Hypothesis (&gt;0.7)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffd43b;"></div>
            <span>Medium Likelihood (0.4-0.7)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #adb5bd;"></div>
            <span>Low Likelihood (&lt;0.4)</span>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(vis_nodes)});
        var edges = new vis.DataSet({json.dumps(vis_edges)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                font: {{
                    size: 14
                }}
            }},
            edges: {{
                smooth: {{
                    type: 'continuous'
                }}
            }},
            physics: {{
                stabilization: true,
                barnesHut: {{
                    gravitationalConstant: -8000,
                    springConstant: 0.001,
                    springLength: 200
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100
            }}
        }};

        var network = new vis.Network(container, data, options);
    </script>

    <div class="info" style="margin-top: 20px;">
        <h3>Instructions</h3>
        <ul>
            <li>Hover over nodes to see full text</li>
            <li>Hover over edges to see relationship type and strength</li>
            <li>Drag nodes to rearrange the layout</li>
            <li>Scroll to zoom in/out</li>
        </ul>
    </div>
</body>
</html>
"""

    # Write to file
    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"✓ Visualization saved to {output_path}")
    print(f"  Open in browser to view the interactive graph")


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_causal_graph.py <causal_graph_data.json>")
        print("\nExample:")
        print("  python visualize_causal_graph.py causal_graph.json")
        sys.exit(1)

    input_path = sys.argv[1]

    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Load graph data
    with open(input_path, 'r') as f:
        graph_data = json.load(f)

    # Generate visualization
    output_path = input_path.replace('.json', '.html')
    generate_html_visualization(graph_data, output_path)


if __name__ == "__main__":
    main()
