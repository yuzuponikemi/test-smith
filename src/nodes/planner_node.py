from src.models import get_planner_model
from src.prompts.planner_prompt import PLANNER_PROMPT
from src.schemas import Plan
from langchain_core.output_parsers import PydanticOutputParser
import re
import json

def planner(state):
    print("---PLANNER---")
    model = get_planner_model()
    parser = PydanticOutputParser(pydantic_object=Plan)
    prompt = PLANNER_PROMPT.partial(format_instructions=parser.get_format_instructions())
    chain = prompt | model
    feedback = state.get("reason", "")
    loop_count = state.get("loop_count", 0)
    response = chain.invoke({"query": state["query"], "feedback": feedback})

    # Extract the JSON object from the response string
    json_match = re.search(r"{\s*\"queries\":\s*\[.*?\]\s*}", response.content, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        plan = json.loads(json_str)
        return {"plan": plan["queries"], "loop_count": loop_count + 1}
    else:
        # Fallback to splitting by newline if no JSON is found
        plan = response.content.split("\n")
        return {"plan": [line for line in plan if line.strip()], "loop_count": loop_count + 1}
