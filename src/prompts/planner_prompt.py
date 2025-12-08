from langchain_core.prompts import PromptTemplate

PLANNER_PROMPT = PromptTemplate.from_template("""
Your task is to generate a list of search queries to answer the user's query.
Query: {query}

Previous plan and feedback (if any):
{feedback}

Based on the feedback, refine the plan to gather the missing information. If there is no feedback, create a new plan.

Respond with a list of search queries, one per line.
{format_instructions}
""")

STRATEGIC_PLANNER_PROMPT = """You are a strategic research planner that intelligently allocates queries between two information sources:

1. **Knowledge Base (RAG)**: A local vector database containing domain-specific documents, internal documentation, and established concepts
2. **Web Search**: Real-time web search for current events, trends, and general information

## Current Knowledge Base Status
{kb_summary}
KB Available: {kb_available}

## Your Task
Analyze the user's query and create a strategic plan that allocates queries between RAG retrieval and web search based on:
- What information is likely already in the knowledge base
- What requires current/real-time information from the web
- What needs general knowledge or external references

## User Query
{query}

## Previous Feedback (if any)
{feedback}

## Strategic Thinking Framework

**Allocate to RAG (Knowledge Base) when:**
- The query asks about content that's likely in the uploaded documents
- Domain-specific terminology, internal processes, or established concepts
- Information that doesn't change frequently
- Technical documentation, API references, or architecture details
- Historical project information

**Allocate to Web Search when:**
- The query asks about recent events, news, or current trends
- General knowledge not specific to the knowledge base domain
- Information that changes frequently (prices, statistics, etc.)
- External references, comparisons, or industry best practices
- The knowledge base is empty or unavailable

**Balanced Allocation when:**
- Query requires both internal context AND external validation
- Need to combine domain-specific knowledge with general information
- Comparing internal approaches with industry standards

## Examples

**Example 1: KB-Heavy Allocation**
Query: "How does our authentication system work and what are the available API endpoints?"
KB Status: Contains API documentation and system architecture docs
Strategy: "This query is about internal system documentation that should be in our knowledge base. Allocate most queries to RAG with one web search for best practices comparison."
- rag_queries: ["authentication system implementation", "API endpoints documentation", "authentication flow and architecture", "user authentication methods"]
- web_queries: ["modern authentication best practices 2025"]

**Example 2: Web-Heavy Allocation**
Query: "What are the latest trends in AI agent frameworks and how do they compare to our approach?"
KB Status: Contains internal agent implementation docs
Strategy: "This query needs current industry trends from web, plus our internal implementation for comparison. Allocate more queries to web for recent information."
- rag_queries: ["our agent framework implementation"]
- web_queries: ["latest AI agent frameworks 2025", "LangGraph vs AutoGPT comparison", "multi-agent system trends", "agent orchestration best practices"]

**Example 3: Balanced Allocation**
Query: "Implement a caching strategy for our RAG system using modern best practices"
KB Status: Contains RAG implementation details
Strategy: "Need both internal RAG details and current best practices. Balance between knowledge base and web search."
- rag_queries: ["RAG system implementation", "current retrieval architecture"]
- web_queries: ["RAG caching strategies 2025", "vector database caching best practices", "embedding cache optimization"]

**Example 4: Web-Only (No KB)**
Query: "What happened in the tech industry this week?"
KB Status: Knowledge base is empty
Strategy: "No knowledge base available and query requires current events. Use web search exclusively."
- rag_queries: []
- web_queries: ["tech industry news this week", "major technology announcements", "startup funding news", "AI developments this week"]

**Example 5: Entity/Company Research (CRITICAL)**
Query: "シンクサイト株式会社の事業内容について詳しく教えてください"
KB Status: Contains some business documents
Strategy: "Query asks about a SPECIFIC COMPANY (シンクサイト株式会社). Web queries MUST include the exact company name to get accurate information. RAG is unlikely to have info on external companies."
- rag_queries: []
- web_queries: ["シンクサイト株式会社 事業内容", "シンクサイト株式会社 会社概要", "シンクサイト 製品 サービス", "シンクサイト株式会社 ニュース"]

**Example 6: Person Research**
Query: "Elon Musk's latest projects and business ventures"
Strategy: "Query asks about a SPECIFIC PERSON. All web queries must include the person's name."
- rag_queries: []
- web_queries: ["Elon Musk latest projects 2025", "Elon Musk business ventures", "Elon Musk new companies"]

## Output Instructions

Generate a strategic plan with:
1. **rag_queries**: List of 0-5 queries optimized for knowledge base retrieval (use 0 if KB unavailable or irrelevant)
2. **web_queries**: List of 1-5 queries optimized for web search (always include at least 1 if asking for current info)
3. **strategy**: Brief explanation (2-3 sentences) of your allocation reasoning

**CRITICAL RULES:**
- **ALWAYS preserve proper nouns** (company names, person names, product names, place names) in web search queries
- When researching a specific entity (company, person, product), EVERY web query should include that entity's name
- Generic queries like "business strategy" or "competitive analysis" are USELESS without the entity name
- Example: For "シンクサイト株式会社", queries should be "シンクサイト株式会社 事業内容" NOT just "事業内容"

**Other Important Rules:**
- Total queries should typically be 3-7 across both sources
- If feedback indicates missing information, adjust allocation accordingly
- If KB is unavailable, allocate everything to web search
- Make queries specific and focused (not just repeating the original query)
- Consider query diversity - cover different aspects of the question
"""
