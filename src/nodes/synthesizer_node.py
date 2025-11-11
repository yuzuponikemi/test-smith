from src.models import get_synthesizer_model
from src.prompts.synthesizer_prompt import SYNTHESIZER_PROMPT

def synthesizer_node(state):
    print("---SYNTHESIZER---")
    model = get_synthesizer_model()

    # Get full context for synthesis
    original_query = state.get("query", "")
    allocation_strategy = state.get("allocation_strategy", "")
    web_queries = state.get("web_queries", [])
    rag_queries = state.get("rag_queries", [])
    analyzed_data = state.get("analyzed_data", [])
    loop_count = state.get("loop_count", 0)

    print(f"  Synthesizing final report from {loop_count} iteration(s)")
    print(f"  Total analyzed data entries: {len(analyzed_data)}")

    prompt = SYNTHESIZER_PROMPT.format(
        original_query=original_query,
        allocation_strategy=allocation_strategy,
        web_queries=web_queries,
        rag_queries=rag_queries,
        analyzed_data=analyzed_data,
        loop_count=loop_count
    )

    message = model.invoke(prompt)
    print("  Report generated successfully")

    return {"report": message.content}
