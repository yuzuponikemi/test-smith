from src.models import get_reflection_model
from src.prompts.reflection_prompt import REFLECTION_PROMPT

def reflection_node(state):
    print("---REFLECTION---")
    model = get_reflection_model()
    prompt = REFLECTION_PROMPT.format(search_results=state["search_results"], query=state["plan"])
    message = model.invoke(prompt)
    return {"reflection": message.content}
