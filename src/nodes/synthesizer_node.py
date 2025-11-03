from src.models import get_synthesizer_model
from src.prompts.synthesizer_prompt import SYNTHESIZER_PROMPT

def synthesizer_node(state):
    print("---SYNTHESIZER---")
    model = get_synthesizer_model()
    prompt = SYNTHESIZER_PROMPT.format(analyzed_data=state["analyzed_data"])
    message = model.invoke(prompt)
    return {"report": message.content}
