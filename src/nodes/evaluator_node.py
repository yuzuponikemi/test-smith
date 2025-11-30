from src.models import get_evaluation_model
from src.prompts.evaluator_prompt import EVALUATOR_PROMPT
from src.schemas import Evaluation
from src.utils.logging_utils import print_node_header


def evaluator_node(state):
    print_node_header("EVALUATOR")
    model = get_evaluation_model()

    # Get context for evaluation
    original_query = state.get("query", "")
    allocation_strategy = state.get("allocation_strategy", "")
    analyzed_data = state.get("analyzed_data", [])
    loop_count = state.get("loop_count", 0)

    print(f"  Evaluating iteration {loop_count}")

    # Use structured output for reliable evaluation
    structured_llm = model.with_structured_output(Evaluation)

    prompt = EVALUATOR_PROMPT.format(
        original_query=original_query,
        allocation_strategy=allocation_strategy,
        analyzed_data=analyzed_data,
        loop_count=loop_count
    )

    try:
        evaluation = structured_llm.invoke(prompt)
        result = "sufficient" if evaluation.is_sufficient else "insufficient"
        print(f"  Result: {result}")
        print(f"  Reason: {evaluation.reason[:100]}...")

        return {
            "evaluation": result,
            "reason": evaluation.reason
        }
    except Exception as e:
        print(f"  Warning: Structured evaluation failed, using fallback: {e}")
        message = model.invoke(prompt)
        return {
            "evaluation": message.content,
            "reason": "Fallback evaluation used"
        }
