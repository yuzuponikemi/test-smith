"""
Code Assistant Node - Retrieves and analyzes code from indexed codebase

This node is specialized for answering questions about code structure,
implementation details, and repository organization using RAG over the
codebase collection.
"""

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

from src.models import get_code_assistant_model
from src.prompts.code_assistant_prompt import CODE_ASSISTANT_PROMPT
from src.utils.embedding_utils import get_embeddings_for_collection
from src.utils.logging_utils import print_node_header


def code_retriever(state):
    """
    Code Retriever Node - Retrieves relevant code chunks from codebase collection

    Searches the indexed codebase for code relevant to the user's query.
    Returns formatted code context with file paths and metadata.
    """
    print_node_header("CODE RETRIEVER")

    query = state.get("query", "")
    code_queries = state.get("code_queries", [query])  # Default to original query
    collection_name = state.get("collection_name", "codebase_collection")

    if not code_queries:
        print("  No code queries - using original query")
        code_queries = [query]

    print(f"  Executing {len(code_queries)} code searches")
    print(f"  Collection: {collection_name}")

    all_results = []

    # Initialize ChromaDB with correct embedding model (from collection metadata)
    persist_directory = "chroma_db"
    embeddings = get_embeddings_for_collection(persist_directory, collection_name)
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    # Configure retriever - get more chunks for code context
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    for query in code_queries:
        print(f"  Searching codebase for: {query}")

        try:
            documents = retriever.get_relevant_documents(query)

            if documents:
                doc_string = f"=== Code Results for '{query}' ===\n\n"

                for i, doc in enumerate(documents, 1):
                    # Extract metadata
                    rel_path = doc.metadata.get('relative_path', doc.metadata.get('source', 'Unknown'))
                    prog_lang = doc.metadata.get('programming_language', 'unknown')
                    doc.metadata.get('filename', '')

                    doc_string += f"[Result {i}]\n"
                    doc_string += f"File: {rel_path}\n"
                    if prog_lang != 'unknown':
                        doc_string += f"Language: {prog_lang}\n"

                    # Format code content
                    doc_string += f"```{prog_lang if prog_lang != 'unknown' else ''}\n"
                    doc_string += doc.page_content
                    doc_string += "\n```\n"
                    doc_string += "---\n"

                all_results.append(doc_string)
                print(f"    Retrieved {len(documents)} code chunks")
            else:
                all_results.append(f"No code found for query: {query}\n")
                print("    No results found")

        except Exception as e:
            print(f"    Error searching for '{query}': {e}")
            all_results.append(f"Error searching codebase: {str(e)}\n")

    print(f"  Completed {len(all_results)} code searches")

    return {"code_results": all_results}


def code_assistant(state):
    """
    Code Assistant Node - Analyzes retrieved code and answers questions

    Takes retrieved code context and generates a helpful response
    addressing the user's question about the codebase.
    """
    print_node_header("CODE ASSISTANT")

    query = state.get("query", "")
    code_results = state.get("code_results", [])

    if not code_results:
        print("  No code results to analyze")
        return {
            "code_response": "I couldn't find any relevant code in the indexed codebase. "
                           "Please make sure the repository has been ingested using "
                           "`python scripts/ingest/ingest_codebase.py`"
        }

    # Combine code results
    code_context = "\n\n".join(code_results)

    print(f"  Analyzing code context ({len(code_context)} chars)")

    # Create prompt
    prompt = PromptTemplate(
        template=CODE_ASSISTANT_PROMPT,
        input_variables=["query", "code_context"]
    )

    # Get model and generate response
    model = get_code_assistant_model()
    chain = prompt | model

    try:
        response = chain.invoke({
            "query": query,
            "code_context": code_context
        })

        # Extract content from response
        result = response.content if hasattr(response, 'content') else str(response)

        print(f"  Generated response ({len(result)} chars)")

        return {"code_response": result}

    except Exception as e:
        print(f"  Error generating response: {e}")
        return {
            "code_response": f"Error analyzing code: {str(e)}\n\n"
                           f"Retrieved code context:\n{code_context[:2000]}..."
        }


def code_query_generator(state):
    """
    Code Query Generator Node - Creates optimized search queries

    Analyzes the user's question and generates multiple search queries
    to find relevant code in the codebase.
    """
    print_node_header("CODE QUERY GENERATOR")

    query = state.get("query", "")

    print(f"  Original query: {query}")

    # Simple query expansion - can be enhanced with LLM
    queries = [query]

    # Extract potential identifiers (function names, class names)
    import re

    # Look for quoted terms
    quoted = re.findall(r'"([^"]+)"', query)
    queries.extend(quoted)

    # Look for camelCase or snake_case terms
    identifiers = re.findall(r'\b([a-z_][a-z_0-9]*(?:_[a-z_0-9]+)+)\b', query.lower())
    identifiers.extend(re.findall(r'\b([A-Z][a-zA-Z0-9]+)\b', query))
    queries.extend(identifiers)

    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q.lower() not in seen and len(q) > 2:
            seen.add(q.lower())
            unique_queries.append(q)

    # Limit to 5 queries
    code_queries = unique_queries[:5]

    print(f"  Generated {len(code_queries)} search queries:")
    for q in code_queries:
        print(f"    - {q}")

    return {"code_queries": code_queries}
