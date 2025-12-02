#!/usr/bin/env python3
"""
Visualize Provenance/Lineage Graph

Creates an interactive HTML visualization showing the research lineage:
- Sources (bottom) → Evidence (middle) → Claims (top)
- Color-coded by node type and confidence levels
- Interactive tooltips with full content
- Clickable nodes for "Why do you say that?" exploration

Usage:
    python scripts/visualization/visualize_provenance_graph.py provenance_graph.json
    python scripts/visualization/visualize_provenance_graph.py provenance_graph.json --output my_lineage.html
"""

import json
import argparse
import sys
from pathlib import Path


def generate_html_visualization(graph_data: dict, output_path: str = "provenance_lineage.html"):
    """Generate an interactive HTML visualization of the provenance graph."""

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    metadata = graph_data.get("metadata", {})

    # Convert nodes to vis.js format with hierarchical layout
    vis_nodes = []
    for node in nodes:
        node_id = node["node_id"]
        node_type = node.get("node_type", "unknown")
        confidence = node.get("metadata", {}).get("confidence", 0.5)

        # Assign colors and shapes based on node type
        if node_type == "source":
            # Sources at bottom - blue shades based on relevance
            relevance = node.get("metadata", {}).get("relevance_score", 0.5)
            if relevance > 0.7:
                color = "#228be6"  # Bright blue
            elif relevance > 0.4:
                color = "#74c0fc"  # Light blue
            else:
                color = "#d0ebff"  # Very light blue
            shape = "database"
            level = 0  # Bottom level

        elif node_type == "evidence":
            # Evidence in middle - green shades based on confidence
            if confidence > 0.7:
                color = "#40c057"  # Green
            elif confidence > 0.4:
                color = "#8ce99a"  # Light green
            else:
                color = "#d3f9d8"  # Very light green
            shape = "box"
            level = 1  # Middle level

        elif node_type == "claim":
            # Claims at top - purple/orange based on confidence
            if confidence > 0.7:
                color = "#7950f2"  # Purple (high confidence)
            elif confidence > 0.4:
                color = "#fab005"  # Yellow/Orange (medium)
            else:
                color = "#ffd43b"  # Light yellow (low)
            shape = "ellipse"
            level = 2  # Top level

        else:
            color = "#adb5bd"  # Gray for unknown
            shape = "dot"
            level = 1

        # Build tooltip with full details
        tooltip_parts = [f"<b>{node.get('label', 'Unknown')}</b>"]
        tooltip_parts.append(f"<br><i>Type: {node_type}</i>")

        if node_type == "source":
            source_type = node.get("metadata", {}).get("source_type", "")
            url = node.get("metadata", {}).get("url", "")
            query = node.get("metadata", {}).get("query_used", "")
            tooltip_parts.append(f"<br>Source type: {source_type}")
            if url:
                tooltip_parts.append(f"<br>URL: {url[:50]}...")
            if query:
                tooltip_parts.append(f"<br>Query: {query[:50]}...")

        elif node_type == "evidence":
            method = node.get("metadata", {}).get("extraction_method", "")
            tooltip_parts.append(f"<br>Method: {method}")
            tooltip_parts.append(f"<br>Confidence: {confidence:.2f}")

        elif node_type == "claim":
            claim_type = node.get("metadata", {}).get("claim_type", "")
            location = node.get("metadata", {}).get("location", "")
            tooltip_parts.append(f"<br>Claim type: {claim_type}")
            tooltip_parts.append(f"<br>Confidence: {confidence:.2f}")
            if location:
                tooltip_parts.append(f"<br>Location: {location}")

        # Add full content preview
        full_content = node.get("full_content", "")
        if full_content:
            preview = full_content[:200] + "..." if len(full_content) > 200 else full_content
            tooltip_parts.append(f"<br><br>{preview}")

        tooltip = "".join(tooltip_parts)

        vis_nodes.append({
            "id": node_id,
            "label": node.get("label", node_id)[:30],
            "color": color,
            "shape": shape,
            "level": level,
            "title": tooltip,
            "font": {"size": 12}
        })

    # Convert edges to vis.js format
    vis_edges = []
    for edge in edges:
        relationship = edge.get("relationship", "related")
        strength = edge.get("strength", 0.5)

        # Edge styling based on relationship type
        if relationship == "derived_from":
            edge_color = "#74c0fc"  # Blue
            dashes = False
        elif relationship == "supports":
            edge_color = "#8ce99a"  # Green
            dashes = False
        else:
            edge_color = "#adb5bd"  # Gray
            dashes = True

        # Edge width based on strength
        width = 1 + (strength * 3)

        vis_edges.append({
            "from": edge.get("source_node_id"),
            "to": edge.get("target_node_id"),
            "color": {"color": edge_color, "opacity": 0.7 + (strength * 0.3)},
            "width": width,
            "dashes": dashes,
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
            "title": f"{relationship} (strength: {strength:.2f})"
        })

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Provenance & Lineage Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8f9fa;
        }}
        #header {{
            background: #343a40;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        #header h1 {{
            margin: 0 0 10px 0;
        }}
        #stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            font-size: 14px;
        }}
        #stats span {{
            background: #495057;
            padding: 5px 15px;
            border-radius: 4px;
        }}
        #graph-container {{
            width: 100%;
            height: calc(100vh - 200px);
            border: 1px solid #dee2e6;
        }}
        #legend {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 15px;
            background: white;
            border-top: 1px solid #dee2e6;
        }}
        .legend-section {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .legend-section h4 {{
            margin: 0;
            font-size: 12px;
            color: #495057;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
        #info-panel {{
            position: fixed;
            top: 100px;
            right: 20px;
            width: 300px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: none;
            max-height: 400px;
            overflow-y: auto;
        }}
        #info-panel h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
        }}
        #info-panel .content {{
            font-size: 12px;
            line-height: 1.5;
        }}
        #close-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            cursor: pointer;
            font-size: 18px;
            color: #868e96;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Research Provenance & Lineage Graph</h1>
        <div id="stats">
            <span>Sources: {metadata.get('total_sources', 0)}</span>
            <span>Evidence: {metadata.get('total_evidence', 0)}</span>
            <span>Claims: {metadata.get('total_claims', 0)}</span>
            <span>Relationships: {metadata.get('total_edges', 0)}</span>
        </div>
    </div>

    <div id="graph-container"></div>

    <div id="legend">
        <div class="legend-section">
            <h4>Node Types:</h4>
            <div class="legend-item">
                <div class="legend-color" style="background: #228be6;"></div>
                Sources
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #40c057;"></div>
                Evidence
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #7950f2;"></div>
                Claims
            </div>
        </div>
        <div class="legend-section">
            <h4>Confidence:</h4>
            <div class="legend-item">
                <div class="legend-color" style="background: #7950f2;"></div>
                High (&gt;0.7)
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #fab005;"></div>
                Medium
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffd43b;"></div>
                Low
            </div>
        </div>
    </div>

    <div id="info-panel">
        <span id="close-panel" onclick="closePanel()">×</span>
        <h3 id="panel-title">Node Details</h3>
        <div id="panel-content" class="content"></div>
    </div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(vis_nodes)});
        var edges = new vis.DataSet({json.dumps(vis_edges)});

        var container = document.getElementById('graph-container');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            layout: {{
                hierarchical: {{
                    direction: 'DU',  // Down to Up
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 100
                }}
            }},
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200
            }},
            nodes: {{
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                smooth: {{
                    type: 'cubicBezier',
                    roundness: 0.4
                }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        // Click handler for detailed info
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                showNodeDetails(node);
            }}
        }});

        function showNodeDetails(node) {{
            document.getElementById('panel-title').textContent = node.label;
            document.getElementById('panel-content').innerHTML = node.title;
            document.getElementById('info-panel').style.display = 'block';
        }}

        function closePanel() {{
            document.getElementById('info-panel').style.display = 'none';
        }}
    </script>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"Visualization saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Visualize Research Provenance & Lineage Graph"
    )
    parser.add_argument(
        "input_file",
        help="Path to JSON file containing provenance graph data"
    )
    parser.add_argument(
        "--output", "-o",
        default="provenance_lineage.html",
        help="Output HTML file path (default: provenance_lineage.html)"
    )

    args = parser.parse_args()

    # Load graph data
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    with open(input_path) as f:
        graph_data = json.load(f)

    # Generate visualization
    generate_html_visualization(graph_data, args.output)
    print(f"\nOpen {args.output} in a browser to view the interactive visualization.")


if __name__ == "__main__":
    main()
