from src.models import get_evaluation_model
from src.prompts.evaluator_prompt import EVALUATOR_PROMPT

def evaluator_node(state):
    print("---EVALUATOR---")
    model = get_evaluation_model()
    prompt = EVALUATOR_PROMPT.format(analyzed_data=state["analyzed_data"])
    message = model.invoke(prompt)
    return {"evaluation": message.content}
