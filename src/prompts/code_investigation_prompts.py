"""
Code Investigation Prompts - Specialized prompts for codebase analysis workflow
"""

CODE_QUERY_ANALYZER_PROMPT = """You are a code investigation query analyzer. Analyze the user's question to determine what to investigate in the codebase.

## User Query
{query}

## Task

Analyze this query and determine:

1. **Investigation Type**: What kind of code investigation is this?
   - dependency: Finding what depends on what
   - flow: Tracing data or control flow
   - usage: Finding where something is used
   - architecture: Understanding design patterns or structure
   - implementation: How something works
   - general: General code questions

2. **Target Elements**: What specific code elements should be investigated?
   - Function names
   - Class names
   - Variable names
   - Module/file names
   - Patterns or concepts

3. **Search Patterns**: What patterns should we search for?
   - Import statements
   - Function calls
   - Class instantiations
   - Variable assignments

4. **Search Queries**: What queries should we use for RAG search?

5. **Investigation Scope**: How broad should the investigation be?
   - narrow: Focus on specific element
   - medium: Include direct relationships
   - broad: Include entire subsystem

## Response Format

Respond with a JSON object:
```json
{{
    "investigation_type": "dependency|flow|usage|architecture|implementation|general",
    "target_elements": ["element1", "element2"],
    "search_patterns": ["pattern1", "pattern2"],
    "code_queries": ["query1", "query2", "query3"],
    "investigation_scope": "narrow|medium|broad",
    "reasoning": "Brief explanation of analysis approach"
}}
```

Analysis:"""


DEPENDENCY_ANALYZER_PROMPT = """You are a code dependency analyzer. Analyze the retrieved code to identify dependencies and relationships between components.

## Investigation Query
{query}

## Target Elements
{target_elements}

## Retrieved Code
{code_context}

## Task

Analyze the code and identify:

1. **Import Dependencies**: What does this code import?
   - Standard library imports
   - Third-party package imports
   - Internal module imports

2. **Class Dependencies**: What classes does this depend on?
   - Parent classes (inheritance)
   - Composed classes (has-a relationships)
   - Used classes (method parameters, return types)

3. **Function Dependencies**: What functions are called?
   - Internal function calls
   - External function calls
   - Callback/handler patterns

4. **Reverse Dependencies**: What might depend on this code?
   - Based on exports
   - Based on public interfaces

5. **Dependency Graph**: Create a structured representation

## Response Format

Respond with a JSON object:
```json
{{
    "dependencies": [
        {{
            "source": "ClassName or function_name",
            "target": "DependencyName",
            "type": "import|inheritance|composition|call|callback",
            "file_path": "path/to/file.py",
            "description": "Brief description"
        }}
    ],
    "import_analysis": [
        {{
            "module": "module.name",
            "imports": ["item1", "item2"],
            "file_path": "path/to/file.py",
            "is_internal": true
        }}
    ],
    "key_findings": [
        "Finding 1 about dependencies",
        "Finding 2 about relationships"
    ],
    "architecture_patterns": ["Pattern 1", "Pattern 2"]
}}
```

Analysis:"""


CODE_FLOW_TRACKER_PROMPT = """You are a code flow analyzer. Analyze the retrieved code to trace data flow and control flow.

## Investigation Query
{query}

## Target Elements
{target_elements}

## Retrieved Code
{code_context}

## Task

Analyze the code and trace:

1. **Data Flow**: How does data move through the code?
   - Input sources (parameters, user input, files, API)
   - Transformations (processing, validation, conversion)
   - Output destinations (return values, storage, API calls)

2. **Control Flow**: How does execution flow?
   - Entry points
   - Conditional branches
   - Loops and iterations
   - Exit points

3. **Variable Usage**: How are key variables used?
   - Where defined
   - Where modified
   - Where read

4. **Function Call Hierarchy**: What's the call stack?
   - Caller functions
   - Callee functions
   - Callback chains

## Response Format

Respond with a JSON object:
```json
{{
    "data_flow": [
        {{
            "variable": "variable_name",
            "source": "where it comes from",
            "transformations": ["step1", "step2"],
            "destination": "where it goes",
            "file_path": "path/to/file.py"
        }}
    ],
    "control_flow": [
        {{
            "entry_point": "function_name",
            "branches": ["branch1", "branch2"],
            "exit_points": ["return", "exception"],
            "file_path": "path/to/file.py"
        }}
    ],
    "variable_usage": [
        {{
            "name": "variable_name",
            "defined_in": "file:line",
            "modified_in": ["file:line1", "file:line2"],
            "read_in": ["file:line1", "file:line2"]
        }}
    ],
    "function_calls": [
        {{
            "caller": "function_name",
            "callee": "called_function",
            "file_path": "path/to/file.py",
            "purpose": "why it's called"
        }}
    ],
    "key_findings": [
        "Finding 1 about flow",
        "Finding 2 about patterns"
    ]
}}
```

Analysis:"""


CODE_INVESTIGATION_SYNTHESIZER_PROMPT = """You are a code investigation report synthesizer. Create a comprehensive report based on the code analysis.

## Original Query
{query}

## Investigation Type
{investigation_type}

## Target Elements
{target_elements}

## Retrieved Code
{code_context}

## Dependency Analysis
{dependency_analysis}

## Flow Analysis
{flow_analysis}

## Key Findings
{key_findings}

## Task

Synthesize all findings into a comprehensive investigation report that:

1. **Directly answers the user's question**
2. **Provides code references** (file:line format)
3. **Shows relevant code snippets** when helpful
4. **Explains relationships** between components
5. **Identifies patterns** and architectural decisions

## Report Structure

### Summary
Brief answer to the investigation question

### Key Components
List of main files/classes/functions involved with their roles

### Dependencies
How components relate to each other (what depends on what)

### Data/Control Flow
How data moves or execution flows through the code

### Code References
Specific code snippets with file paths

### Recommendations
Any suggestions for understanding or working with this code

## Guidelines

- Be technical and precise - this is for developers
- Always cite file paths and line numbers
- Use code blocks for snippets
- If information is missing, note what else to investigate
- Focus on answering the original question

Report:"""
