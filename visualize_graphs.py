"""
Graph Visualization Generator using LangGraph's native methods

This script generates visual diagrams for all registered graph workflows
using LangGraph's built-in visualization capabilities.

Usage:
    python visualize_graphs.py

Output:
    - Creates graph_visualizations/ directory
    - Generates PNG images for each graph using draw_mermaid_png()
    - Falls back to ASCII if PNG generation fails
"""

import os
from pathlib import Path
from src.graphs import list_graphs, get_graph


def ensure_output_dir(base_dir: str = "graph_visualizations") -> Path:
    """Create output directory if it doesn't exist."""
    output_path = Path(base_dir)
    output_path.mkdir(exist_ok=True)
    return output_path


def generate_graph_visualization(graph_name: str, builder, output_dir: Path):
    """
    Generate visualization for a graph using LangGraph's native methods.

    Args:
        graph_name: Name of the graph
        builder: Graph builder instance
        output_dir: Output directory path
    """
    print(f"Processing: {graph_name}")
    print("-" * 40)

    try:
        # Get the compiled graph
        compiled_graph = builder.build()
        graph_drawable = compiled_graph.get_graph()

        # Try to generate PNG using Mermaid
        png_path = output_dir / f"{graph_name}_graph.png"
        try:
            png_data = graph_drawable.draw_mermaid_png()
            with open(png_path, 'wb') as f:
                f.write(png_data)
            print(f"✓ Generated PNG: {png_path}")
        except Exception as e:
            print(f"  ⚠ PNG generation failed: {e}")
            print(f"  Trying alternative method...")

            # Try alternative PNG method
            try:
                png_data = graph_drawable.draw_png()
                with open(png_path, 'wb') as f:
                    f.write(png_data)
                print(f"✓ Generated PNG (graphviz): {png_path}")
            except Exception as e2:
                print(f"  ⚠ Alternative PNG failed: {e2}")

                # Fall back to saving Mermaid diagram
                mermaid_path = output_dir / f"{graph_name}_graph.mmd"
                mermaid_data = graph_drawable.draw_mermaid()
                with open(mermaid_path, 'w') as f:
                    f.write(mermaid_data)
                print(f"✓ Saved Mermaid diagram: {mermaid_path}")
                print(f"  View at: https://mermaid.live/")

        # Also generate ASCII representation
        ascii_path = output_dir / f"{graph_name}_graph.txt"
        ascii_data = graph_drawable.draw_ascii()
        with open(ascii_path, 'w') as f:
            f.write(ascii_data)
        print(f"✓ Generated ASCII: {ascii_path}")

        print()
        return True

    except Exception as e:
        print(f"✗ Error processing {graph_name}: {str(e)}\n")
        return False


def generate_index(output_dir: Path, graphs: dict, results: dict):
    """
    Generate an index file with links to all visualizations.

    Args:
        output_dir: Output directory path
        graphs: Dictionary of graph metadata
        results: Dictionary of successful generations
    """
    index_file = output_dir / "README.md"

    with open(index_file, 'w') as f:
        f.write("# Test-Smith Graph Visualizations\n\n")
        f.write("This directory contains visual diagrams for all registered graph workflows.\n\n")
        f.write(f"**Generated:** {sum(results.values())} / {len(graphs)} graphs\n\n")

        f.write("## Available Graphs\n\n")

        for graph_name, metadata in graphs.items():
            f.write(f"### {metadata.get('name', graph_name)}\n\n")
            f.write(f"{metadata.get('description', 'No description')}\n\n")
            f.write(f"- **Complexity:** {metadata.get('complexity', 'N/A')}\n")
            f.write(f"- **Version:** {metadata.get('version', 'N/A')}\n\n")

            # Link to files if they exist
            png_file = f"{graph_name}_graph.png"
            mmd_file = f"{graph_name}_graph.mmd"
            txt_file = f"{graph_name}_graph.txt"

            f.write("**Files:**\n")
            if (output_dir / png_file).exists():
                f.write(f"- 🖼️ [{png_file}](./{png_file}) (PNG image)\n")
            if (output_dir / mmd_file).exists():
                f.write(f"- 📊 [{mmd_file}](./{mmd_file}) (Mermaid diagram)\n")
            if (output_dir / txt_file).exists():
                f.write(f"- 📝 [{txt_file}](./{txt_file}) (ASCII diagram)\n")
            f.write("\n")

        f.write("## Graph Comparison\n\n")
        f.write("| Graph | Complexity | Best For |\n")
        f.write("|-------|-----------|----------|\n")

        for graph_name, metadata in graphs.items():
            name = metadata.get('name', graph_name)
            complexity = metadata.get('complexity', 'N/A')
            use_case = metadata.get('use_cases', ['N/A'])[0] if metadata.get('use_cases') else 'N/A'
            f.write(f"| {name} | {complexity} | {use_case} |\n")

    print(f"✓ Generated index: {index_file}")


def main():
    """Main function to generate visualizations for all graphs."""
    print("=" * 80)
    print("GRAPH VISUALIZATION GENERATOR (Using LangGraph Native Methods)")
    print("=" * 80 + "\n")

    # Create output directory
    output_dir = ensure_output_dir()
    print(f"Output directory: {output_dir.absolute()}\n")

    # Get all registered graphs
    graphs = list_graphs()
    print(f"Found {len(graphs)} registered graphs\n")

    results = {}

    # Generate visualization for each graph
    for graph_name, metadata in graphs.items():
        success = generate_graph_visualization(graph_name, get_graph(graph_name), output_dir)
        results[graph_name] = success

    # Generate index file
    generate_index(output_dir, graphs, results)

    # Print summary
    print("=" * 80)
    successful = sum(results.values())
    print(f"Successfully generated {successful}/{len(graphs)} visualizations")
    print(f"Location: {output_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
