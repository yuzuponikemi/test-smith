"""
Prompts for Term Definer Node

These prompts extract technical terms from queries and generate
verified definitions to prevent topic drift.
"""

TERM_EXTRACTOR_PROMPT = """You are a technical term extractor. Your job is to identify terms in the query that:
1. Are proper nouns (product names, company names, framework names)
2. Are technical jargon that could be misunderstood
3. Are acronyms or abbreviations
4. Are domain-specific concepts

## Query
{query}

## Your Task

Extract ALL terms that need definition verification. Focus on:
- Product/tool names (e.g., "LangSmith", "ChromaDB", "Kubernetes")
- Framework/library names (e.g., "LangChain", "React", "TensorFlow")
- Technical concepts (e.g., "RAG", "vector embedding", "containerization")
- Company/organization names that might be confused
- Acronyms (e.g., "LLM", "API", "CI/CD")

DO NOT extract:
- Common words everyone knows
- Generic industry terms (e.g., "software", "development")
- Simple adjectives or verbs

## Output

Return a list of terms that need definition lookup.
If the query is simple with no special terms, return an empty list.

Examples:
- "LangSmithの製造業への活用" → ["LangSmith"]
- "Kubernetesでのマイクロサービスデプロイ" → ["Kubernetes", "マイクロサービス"]
- "今日の天気は？" → []
"""

TERM_DEFINITION_PROMPT = """You are a technical term definition expert. Your job is to provide accurate, verified definitions for technical terms.

## Term to Define
{term}

## Original Query Context
{query}

## Search Results (Reference Material)
{search_results}

## Your Task

Based on the search results and your knowledge, provide:
1. **category**: What type of thing is this? (tool, framework, company, concept, protocol, etc.)
2. **definition**: A clear, accurate 1-2 sentence definition
3. **key_features**: 3-5 key characteristics or features
4. **common_confusions**: Things this term is commonly confused with
5. **confidence**: How confident are you in this definition? (high/medium/low)

## CRITICAL RULES

1. **Prioritize official/authoritative sources** from search results
2. **If the term is a product name**, identify the company that makes it
3. **If the term could mean multiple things**, choose the most likely meaning given the query context
4. **If search results are unclear or contradictory**, set confidence to "low"
5. **Never guess** - if you don't know, say so

## Examples

Term: "LangSmith"
Query: "LangSmithの活用パターン"
→ category: "tool"
→ definition: "LangSmith is LangChain's observability and evaluation platform for LLM applications, providing tracing, debugging, and testing capabilities."
→ key_features: ["LLM application tracing", "Prompt debugging", "Evaluation datasets", "Production monitoring", "Integration with LangChain"]
→ common_confusions: ["Not a person named Smith", "Not the LangChain framework itself", "Not a language model"]
→ confidence: "high"

Term: "RAG"
Query: "RAGシステムの構築"
→ category: "concept"
→ definition: "Retrieval-Augmented Generation (RAG) is an AI framework that combines information retrieval with text generation to ground LLM responses in external knowledge."
→ key_features: ["Retrieval component", "Generation component", "External knowledge integration", "Reduced hallucination"]
→ common_confusions: ["Not 'random'", "Not a specific product"]
→ confidence: "high"

Now define the term based on the search results provided.
"""
