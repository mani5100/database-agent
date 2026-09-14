"""Generate a visual diagram of the LangGraph agent workflow.

Renders the compiled StateGraph from `database_agent.graph.builder` to:
  - docs/assets/agent_graph.mmd  (Mermaid source, embedded in README.md)
  - docs/assets/agent_graph.png  (rendered image, best-effort, requires network access)

Usage:
    uv run python scripts/generate_agent_graph.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from database_agent.graph.builder import build_agent_graph

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "assets"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    graph = build_agent_graph()
    drawable = graph.get_graph()

    mermaid_source = drawable.draw_mermaid()
    mmd_path = OUTPUT_DIR / "agent_graph.mmd"
    mmd_path.write_text(mermaid_source, encoding="utf-8")
    print(f"Wrote Mermaid source to {mmd_path}")

    png_path = OUTPUT_DIR / "agent_graph.png"
    try:
        drawable.draw_mermaid_png(output_file_path=str(png_path))
        print(f"Wrote PNG diagram to {png_path}")
    except Exception as exc:  # network call to mermaid.ink can fail offline
        print(f"Skipped PNG render ({exc}). Mermaid source is still available at {mmd_path}.")


if __name__ == "__main__":
    main()
