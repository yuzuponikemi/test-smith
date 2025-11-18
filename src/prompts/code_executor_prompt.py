"""Prompt templates for code execution node."""

from langchain.prompts import PromptTemplate

# Prompt for detecting if code execution is needed
CODE_NEEDS_DETECTOR_TEMPLATE = """You are a research assistant that determines when Python code execution would be beneficial for answering a query.

Analyze the following research context and determine if code execution is needed.

ORIGINAL QUERY:
{query}

ANALYZED DATA AVAILABLE:
{analyzed_data}

WHEN CODE EXECUTION IS BENEFICIAL:
1. Quantitative analysis - calculations, statistics, growth rates, comparisons
2. Data processing - parsing CSV/JSON data, filtering, aggregation
3. Visualization needs - charts, graphs, plots
4. Mathematical verification - formulas, equations, proofs
5. Pattern analysis - trends, correlations, distributions
6. Benchmark comparisons - performance metrics requiring computation
7. Text analysis - sentiment analysis, word frequency, NLP tasks

WHEN CODE EXECUTION IS NOT NEEDED:
1. Qualitative questions - opinions, explanations, definitions
2. Simple factual questions - dates, names, descriptions
3. Conceptual understanding - how things work, theory
4. Insufficient data - no numerical data to process

Analyze the query and available data to determine:
1. Is code execution beneficial for this query?
2. If yes, what specific computation or analysis should be performed?
3. What data from the analyzed results should be used?

Respond with your analysis."""

CODE_NEEDS_DETECTOR_PROMPT = PromptTemplate(
    template=CODE_NEEDS_DETECTOR_TEMPLATE,
    input_variables=["query", "analyzed_data"]
)


# Prompt for generating Python code
CODE_GENERATOR_TEMPLATE = """You are an expert Python programmer generating code for research analysis.

TASK DESCRIPTION:
{task_description}

DATA TO PROCESS:
{data_context}

REQUIREMENTS:
1. Write clean, efficient Python code
2. Use standard libraries: pandas, numpy, matplotlib, seaborn, scipy, requests
3. Include proper error handling
4. Print results clearly with descriptive labels
5. If creating visualizations, save to file (not display)
6. Code must be self-contained and executable
7. Parse any data provided in the context
8. Include comments explaining key steps

OUTPUT FORMAT:
- Generate ONLY executable Python code
- No markdown code blocks
- No explanations outside the code
- All output should use print() statements
- Save any plots to 'output_plot.png'

Write the Python code to accomplish this task:"""

CODE_GENERATOR_PROMPT = PromptTemplate(
    template=CODE_GENERATOR_TEMPLATE,
    input_variables=["task_description", "data_context"]
)


# Prompt for analyzing code execution results
CODE_RESULT_ANALYZER_TEMPLATE = """You are a research analyst interpreting code execution results.

ORIGINAL QUERY:
{query}

TASK PERFORMED:
{task_description}

CODE EXECUTED:
```python
{code}
```

EXECUTION OUTPUT:
{execution_output}

EXECUTION STATUS: {execution_status}
{error_message}

YOUR TASK:
1. Interpret the execution results in the context of the original query
2. Extract key findings and insights
3. If there were errors, explain what went wrong
4. Summarize the quantitative results in human-readable format
5. Note any limitations or caveats
6. If visualizations were created, describe them

Provide a clear, concise analysis of the results:"""

CODE_RESULT_ANALYZER_PROMPT = PromptTemplate(
    template=CODE_RESULT_ANALYZER_TEMPLATE,
    input_variables=["query", "task_description", "code", "execution_output",
                     "execution_status", "error_message"]
)
