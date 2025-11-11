from pydantic import BaseModel, Field
from typing import List

class Plan(BaseModel):
    """A plan to answer the user's query."""
    queries: List[str] = Field(description="A list of search queries to answer the user's query.")

class StrategicPlan(BaseModel):
    """Strategic plan with intelligent query allocation between RAG and web sources."""

    rag_queries: List[str] = Field(
        description="Queries for knowledge base retrieval (domain-specific content, internal documentation, established concepts)"
    )
    web_queries: List[str] = Field(
        description="Queries for web search (recent events, current trends, general information, external sources)"
    )
    strategy: str = Field(
        description="Reasoning for this allocation: What information is likely in KB vs needs web? Why this distribution?"
    )

class Evaluation(BaseModel):
    """An evaluation of the sufficiency of the information."""
    is_sufficient: bool = Field(description="Whether the information is sufficient to create a comprehensive report.")
    reason: str = Field(description="The reason for the evaluation.")
