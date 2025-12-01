"""
Tests for Graph Selector - Automatic graph selection based on query analysis

Coverage target: 100%
Testing strategy: AAA pattern with comprehensive edge cases
"""

import pytest
from src.utils.graph_selector import (
    GraphType,
    detect_code_execution_need,
    detect_causal_inference_need,
    detect_comparative_need,
    detect_fact_check_need,
    detect_simple_query,
    auto_select_graph,
    explain_selection,
)


# ============================================================================
# Test detect_code_execution_need()
# ============================================================================


class TestDetectCodeExecutionNeed:
    """Test code execution detection logic"""

    def test_calculation_keywords(self):
        """Should detect calculation keywords"""
        queries = [
            "Calculate the total revenue",
            "Compute the average score",
            "What is the sum of all values",
            "Find the mean temperature",
            "Show me the median price",
            "What percentage of users clicked?",
            "Calculate the ratio between A and B",
            "Analyze the growth rate",
            "Show me the trend over time",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is True

    def test_visualization_keywords(self):
        """Should detect visualization keywords"""
        queries = [
            "Create a chart showing sales",
            "Plot the distribution",
            "Visualize the data",
            "Show me a graph of temperature",
            "Generate a histogram",
            "Draw a diagram of the process",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is True

    def test_math_expressions(self):
        """Should detect mathematical expressions"""
        queries = [
            "What is 15 + 25?",
            "Calculate 100 - 37",
            "Compute 12 * 8",
            "What is 144 / 12?",
            "Find 25 % 7",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is True

    def test_data_analysis_keywords(self):
        """Should detect data analysis keywords"""
        queries = [
            "Analyze data from the report",
            "Process data and show results",
            "Parse this CSV file",
            "Show statistical correlation",
            "Run regression analysis",
            "How many users signed up?",
            "How much did we earn?",
            "Count the total number of items",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is True

    def test_case_insensitive_matching(self):
        """Should be case insensitive"""
        queries = [
            "CALCULATE the total",
            "Compute THE AVERAGE",
            "Show Me A CHART",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is True

    def test_no_code_execution_needed(self):
        """Should return False for non-computational queries"""
        queries = [
            "What is quantum computing?",
            "Explain photosynthesis",
            "Tell me about history of Rome",
            "Who invented the telephone?",
        ]
        for query in queries:
            assert detect_code_execution_need(query) is False

    def test_empty_query(self):
        """Should handle empty query gracefully"""
        assert detect_code_execution_need("") is False


# ============================================================================
# Test detect_causal_inference_need()
# ============================================================================


class TestDetectCausalInferenceNeed:
    """Test causal inference detection logic"""

    def test_why_questions(self):
        """Should detect 'why' questions"""
        queries = [
            "Why is the server slow?",
            "Why did the deployment fail?",
            "Why are users leaving?",
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is True

    def test_multilingual_why(self):
        """Should detect multilingual 'why' keywords"""
        queries = [
            "理由を教えてください",  # Japanese "reason"
            "причина этой проблемы",  # Russian "cause"
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is True

    def test_root_cause_keywords(self):
        """Should detect root cause analysis keywords"""
        queries = [
            "Find the root cause of the error",
            "What is the cause of high latency?",
            "What's the reason for this failure?",
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is True

    def test_troubleshooting_keywords(self):
        """Should detect troubleshooting keywords"""
        queries = [
            "Troubleshoot the database connection",
            "Debug this Python script",
            "Diagnose the performance issue",
            "Fix this broken feature",
            "Investigate this error message",
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is True

    def test_failure_keywords(self):
        """Should detect failure-related keywords"""
        queries = [
            "Why is this feature not working?",
            "What's causing this bug?",
            "Analyze this issue in production",
            "Why is the API broken?",
            "Find the problem with authentication",
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is True

    def test_no_causal_inference_needed(self):
        """Should return False for non-troubleshooting queries"""
        queries = [
            "What is machine learning?",
            "How to create a React app?",
            "List the features of Python",
        ]
        for query in queries:
            assert detect_causal_inference_need(query) is False

    def test_empty_query(self):
        """Should handle empty query gracefully"""
        assert detect_causal_inference_need("") is False


# ============================================================================
# Test detect_comparative_need()
# ============================================================================


class TestDetectComparativeNeed:
    """Test comparative analysis detection logic"""

    def test_vs_pattern(self):
        """Should detect 'vs' pattern"""
        queries = [
            "React vs Vue",
            "Python vs JavaScript",
            "MySQL vs PostgreSQL",
        ]
        for query in queries:
            assert detect_comparative_need(query) is True

    def test_versus_pattern(self):
        """Should detect 'versus' keyword"""
        queries = [
            "AWS versus Azure",
            "REST versus GraphQL",
        ]
        for query in queries:
            assert detect_comparative_need(query) is True

    def test_comparison_keywords(self):
        """Should detect comparison keywords"""
        queries = [
            "Compare React and Vue",
            "What's the difference between SQL and NoSQL?",
            "Show similarities between Java and C#",
            "Which is better: Docker or Podman?",
            "Choose between MongoDB and Cassandra",
            "Decide between TypeScript and JavaScript",
        ]
        for query in queries:
            assert detect_comparative_need(query) is True

    def test_pros_cons_keywords(self):
        """Should detect pros/cons and trade-off keywords"""
        queries = [
            "What are the pros and cons of microservices?",
            "Analyze the trade-offs of using Redis",
            "Show tradeoff between speed and accuracy",
        ]
        for query in queries:
            assert detect_comparative_need(query) is True

    def test_better_worse_keywords(self):
        """Should detect better/worse comparisons"""
        queries = [
            "Is Python better than Ruby?",
            "Why is X worse than Y?",
        ]
        for query in queries:
            assert detect_comparative_need(query) is True

    def test_no_comparative_needed(self):
        """Should return False for non-comparative queries"""
        queries = [
            "What is Docker?",
            "How to install Python?",
            "Explain neural networks",
        ]
        for query in queries:
            assert detect_comparative_need(query) is False

    def test_empty_query(self):
        """Should handle empty query gracefully"""
        assert detect_comparative_need("") is False


# ============================================================================
# Test detect_fact_check_need()
# ============================================================================


class TestDetectFactCheckNeed:
    """Test fact checking detection logic"""

    def test_true_false_questions(self):
        """Should detect true/false verification questions"""
        queries = [
            "Is it true that Python is slower than C++?",
            "Is this true about quantum computing?",
            "True or false: AI can replace programmers",
        ]
        for query in queries:
            assert detect_fact_check_need(query) is True

    def test_verification_keywords(self):
        """Should detect verification keywords"""
        queries = [
            "Fact check this claim about vaccines",
            "Verify if this statement is correct",
            "Is this information accurate?",
            "Confirm that Docker uses containers",
            "Validate this assumption",
        ]
        for query in queries:
            assert detect_fact_check_need(query) is True

    def test_multilingual_fact_check(self):
        """Should detect multilingual fact-check keywords"""
        queries = [
            "この情報は本当ですか？",  # Japanese "is this true?"
            "真偽を確認してください",  # Japanese "verify true/false"
        ]
        for query in queries:
            assert detect_fact_check_need(query) is True

    def test_no_fact_check_needed(self):
        """Should return False for non-verification queries"""
        queries = [
            "What is quantum computing?",
            "How does Docker work?",
            "Explain the concept of recursion",
        ]
        for query in queries:
            assert detect_fact_check_need(query) is False

    def test_empty_query(self):
        """Should handle empty query gracefully"""
        assert detect_fact_check_need("") is False


# ============================================================================
# Test detect_simple_query()
# ============================================================================


class TestDetectSimpleQuery:
    """Test simple query detection logic"""

    def test_very_short_queries(self):
        """Should detect very short queries (<50 chars)"""
        queries = [
            "What is AI?",
            "Define recursion",
            "Python basics",
        ]
        for query in queries:
            assert detect_simple_query(query) is True
            assert len(query) < 50

    def test_single_sentence_short_queries(self):
        """Should detect single sentence queries under 100 chars"""
        query = "What are the main features of Python programming language?"
        assert detect_simple_query(query) is True
        assert len(query) < 100

    def test_complex_multi_sentence_queries(self):
        """Should reject multi-sentence queries"""
        query = "Explain quantum computing. How does it work? What are the applications?"
        assert detect_simple_query(query) is False

    def test_long_single_sentence_queries(self):
        """Should reject long single-sentence queries (>100 chars)"""
        query = (
            "What are the detailed architectural differences between microservices "
            "and monolithic applications in modern cloud environments?"
        )
        assert detect_simple_query(query) is False
        assert len(query) > 100

    def test_empty_query(self):
        """Should handle empty query gracefully"""
        assert detect_simple_query("") is True  # Very short


# ============================================================================
# Test auto_select_graph()
# ============================================================================


class TestAutoSelectGraph:
    """Test automatic graph selection logic"""

    def test_code_execution_priority(self):
        """Code execution should have highest priority"""
        query = "Calculate the average and plot a chart"
        result = auto_select_graph(query)
        assert result == "code_execution"

    def test_causal_inference_priority(self):
        """Causal inference should have second priority"""
        query = "Why is my application slow?"
        result = auto_select_graph(query)
        assert result == "causal_inference"

    def test_comparative_priority(self):
        """Comparative should have third priority"""
        query = "Compare React vs Vue frameworks"
        result = auto_select_graph(query)
        assert result == "comparative"

    def test_fact_check_priority(self):
        """Fact check should have fourth priority"""
        query = "Is it true that Python is dynamically typed?"
        result = auto_select_graph(query)
        assert result == "fact_check"

    def test_quick_research_priority(self):
        """Quick research for simple queries"""
        query = "What is Docker?"
        result = auto_select_graph(query)
        assert result == "quick_research"

    def test_deep_research_default(self):
        """Complex queries should default to deep_research"""
        query = (
            "Explain the comprehensive architectural patterns used in modern "
            "distributed systems and their implications for scalability."
        )
        result = auto_select_graph(query)
        assert result == "deep_research"

    def test_priority_override(self):
        """Higher priority should override lower priority"""
        # This query matches both code_execution and causal_inference
        # Code execution should win (higher priority)
        query = "Why is my calculation wrong? Calculate the average and sum."
        result = auto_select_graph(query)
        assert result == "code_execution"

    def test_custom_default_parameter(self):
        """Should respect custom default parameter"""
        query = "Explain the philosophical implications of epistemological frameworks in contemporary discourse"
        result = auto_select_graph(query, default="quick_research")
        # Long complex query doesn't match simple pattern, should use custom default
        assert result == "quick_research"

    def test_empty_query_uses_default(self):
        """Empty query should use quick_research (detected as simple)"""
        # Empty string has length < 50, so detect_simple_query returns True
        result = auto_select_graph("")
        assert result == "quick_research"


# ============================================================================
# Test explain_selection()
# ============================================================================


class TestExplainSelection:
    """Test selection explanation generation"""

    def test_code_execution_explanation(self):
        """Should explain code execution selection"""
        query = "Calculate the average temperature"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "code_execution" in explanation
        assert "computational" in explanation.lower() or "analytical" in explanation.lower()

    def test_causal_inference_explanation(self):
        """Should explain causal inference selection"""
        query = "Why is the server slow?"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "causal_inference" in explanation
        assert "causal reasoning" in explanation.lower() or "troubleshooting" in explanation.lower()

    def test_comparative_explanation(self):
        """Should explain comparative selection"""
        query = "Compare React vs Vue"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "comparative" in explanation
        assert "comparison" in explanation.lower() or "trade-off" in explanation.lower()

    def test_fact_check_explanation(self):
        """Should explain fact check selection"""
        query = "Is it true that Python is dynamically typed?"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "fact_check" in explanation
        assert "verification" in explanation.lower() or "fact" in explanation.lower()

    def test_quick_research_explanation(self):
        """Should explain quick research selection"""
        query = "What is Docker?"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "quick_research" in explanation
        assert "simple" in explanation.lower() or "concise" in explanation.lower()

    def test_deep_research_explanation(self):
        """Should explain deep research selection (default)"""
        # Use a long multi-sentence query to trigger deep_research
        query = "Explain the comprehensive architecture of modern distributed systems. How do they scale? What are the key design patterns?"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        assert "deep_research" in explanation
        assert "complex" in explanation.lower() or "multi-faceted" in explanation.lower()

    def test_multiple_reasons(self):
        """Should list multiple reasons when query matches multiple patterns"""
        # This query matches code_execution (calculate), causal_inference (why), and comparative (compare)
        query = "Why is it slow? Calculate the average and compare different approaches."
        selected = auto_select_graph(query)  # Should select code_execution (priority 1)
        explanation = explain_selection(query, selected)

        # All three patterns should be mentioned in the explanation
        assert "computational" in explanation.lower() or "analytical" in explanation.lower()
        assert "causal" in explanation.lower() or "troubleshooting" in explanation.lower()
        assert "comparison" in explanation.lower() or "trade-off" in explanation.lower()

    def test_explanation_format(self):
        """Should have proper explanation format"""
        query = "Calculate the average"
        selected = auto_select_graph(query)
        explanation = explain_selection(query, selected)

        # Should have the graph name
        assert selected in explanation
        # Should have bullet points
        assert "  - " in explanation
