from src.models import get_analyzer_model
from src.prompts.analyzer_prompt import ANALYZER_PROMPT

def analyzer_node(state):
    print("---ANALYZER---")
    model = get_analyzer_model()
    
    # Combine search results and RAG results
    all_results = state["search_results"] + state.get("rag_results", [])
    
    prompt = ANALYZER_PROMPT.format(search_results=all_results)
    message = model.invoke(prompt)
    return {"analyzed_data": [message.content]}
