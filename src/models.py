from langchain_ollama.chat_models import ChatOllama

def get_planner_model():
    return ChatOllama(model="llama3")

def get_master_planner_model():
    """
    Model for Master Planner (hierarchical decomposition)
    Uses command-r for better structured output generation
    """
    return ChatOllama(model="command-r")

def get_reflection_model():
    return ChatOllama(model="llama3")

def get_evaluation_model():
    return ChatOllama(model="command-r")

def get_analyzer_model():
    return ChatOllama(model="llama3")

def get_synthesizer_model():
    return ChatOllama(model="llama3")
