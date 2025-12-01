"""
Unit tests for recursion_budget module.

Tests budget calculation and tracking for recursion control.
"""

import pytest

from src.utils.recursion_budget import (
    calculate_recursion_budget,
    increment_execution_count,
    log_budget_status,
)


class TestCalculateRecursionBudget:
    """Test recursion budget calculation."""

    def test_calculate_budget_healthy_status(self):
        """Test budget calculation with healthy usage (<50%)."""
        state = {
            "node_execution_count": 30,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2", "task3"]},
            "current_subtask_index": 1,
        }

        result = calculate_recursion_budget(state)

        # 30/150 = 20% usage
        assert result["status"] == "healthy"
        assert result["current_count"] == 30
        assert result["limit"] == 150
        assert result["remaining"] == 120
        assert result["usage_percent"] == 20.0
        assert result["recommendations"]["allow_drill_down"] is True
        assert result["recommendations"]["allow_plan_revision"] is True

    def test_calculate_budget_caution_status(self):
        """Test budget calculation with caution status (50-70%)."""
        state = {
            "node_execution_count": 90,  # 60% of 150
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2", "task3", "task4", "task5"]},
            "current_subtask_index": 3,  # 2 remaining
        }

        result = calculate_recursion_budget(state)

        assert result["status"] == "caution"
        assert result["usage_percent"] == 60.0
        assert result["remaining_subtasks"] == 2
        # Only allow drill-down if few subtasks left
        assert result["recommendations"]["max_new_subtasks"] == 2

    def test_calculate_budget_warning_status(self):
        """Test budget calculation with warning status (70-90%)."""
        state = {
            "node_execution_count": 120,  # 80% of 150
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2"]},
            "current_subtask_index": 1,
        }

        result = calculate_recursion_budget(state)

        assert result["status"] == "warning"
        assert result["usage_percent"] == 80.0
        assert result["recommendations"]["allow_drill_down"] is False
        assert result["recommendations"]["allow_plan_revision"] is True
        assert result["recommendations"]["max_new_subtasks"] == 1

    def test_calculate_budget_critical_status(self):
        """Test budget calculation with critical status (>=90%)."""
        state = {
            "node_execution_count": 140,  # 93% of 150
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1"]},
            "current_subtask_index": 0,
        }

        result = calculate_recursion_budget(state)

        assert result["status"] == "critical"
        assert result["usage_percent"] >= 90.0
        assert result["recommendations"]["allow_drill_down"] is False
        assert result["recommendations"]["allow_plan_revision"] is False
        assert result["recommendations"]["max_new_subtasks"] == 0

    def test_calculate_budget_no_master_plan(self):
        """Test budget calculation without master plan."""
        state = {
            "node_execution_count": 50,
            "recursion_limit": 150,
        }

        result = calculate_recursion_budget(state)

        assert result["remaining_subtasks"] == 0
        assert "usage_percent" in result
        assert result["status"] in ["healthy", "caution", "warning", "critical"]

    def test_calculate_budget_default_limit(self):
        """Test budget calculation with default recursion limit."""
        state = {
            "node_execution_count": 50,
        }

        result = calculate_recursion_budget(state)

        assert result["limit"] == 150  # Default limit
        assert result["remaining"] == 100

    def test_calculate_budget_zero_limit(self):
        """Test budget calculation with zero limit (edge case)."""
        state = {
            "node_execution_count": 10,
            "recursion_limit": 0,
        }

        result = calculate_recursion_budget(state)

        assert result["usage_percent"] == 100  # Should handle division by zero
        assert result["limit"] == 0

    def test_calculate_budget_zero_current_index(self):
        """Test budget calculation when current_subtask_index is 0."""
        state = {
            "node_execution_count": 20,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2"]},
            "current_subtask_index": 0,
        }

        result = calculate_recursion_budget(state)

        # Should handle division by zero
        assert result["avg_per_subtask"] == 10  # Default value
        assert "estimated_total_needed" in result

    def test_calculate_budget_will_exceed_prediction(self):
        """Test prediction of budget exceeding."""
        state = {
            "node_execution_count": 100,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2", "task3", "task4"]},
            "current_subtask_index": 1,  # 3 remaining
        }

        result = calculate_recursion_budget(state)

        # 100 + (3 * 100/1) = 400, which exceeds 150
        assert result["will_exceed"] is True
        assert result["estimated_total_needed"] > result["limit"]

    def test_calculate_budget_will_not_exceed_prediction(self):
        """Test prediction of budget not exceeding."""
        state = {
            "node_execution_count": 30,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2", "task3"]},
            "current_subtask_index": 2,  # 1 remaining
        }

        result = calculate_recursion_budget(state)

        # 30 + (1 * 30/2) = 45, which does not exceed 150
        assert result["will_exceed"] is False

    def test_calculate_budget_edge_cases_at_boundaries(self):
        """Test budget calculation at exact boundaries."""
        # Test at 50% boundary (healthy -> caution)
        state_50 = {
            "node_execution_count": 75,
            "recursion_limit": 150,
        }
        result_50 = calculate_recursion_budget(state_50)
        assert result_50["usage_percent"] == 50.0
        assert result_50["status"] == "caution"

        # Test at 70% boundary (caution -> warning)
        state_70 = {
            "node_execution_count": 105,
            "recursion_limit": 150,
        }
        result_70 = calculate_recursion_budget(state_70)
        assert result_70["usage_percent"] == 70.0
        assert result_70["status"] == "warning"

        # Test at 90% boundary (warning -> critical)
        state_90 = {
            "node_execution_count": 135,
            "recursion_limit": 150,
        }
        result_90 = calculate_recursion_budget(state_90)
        assert result_90["usage_percent"] == 90.0
        assert result_90["status"] == "critical"

    def test_calculate_budget_caution_drill_down_logic(self):
        """Test drill-down logic in caution state."""
        # Few subtasks left (<=3) - should allow drill-down
        state_few = {
            "node_execution_count": 90,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["task1", "task2", "task3", "task4"]},
            "current_subtask_index": 2,  # 2 remaining
        }
        result_few = calculate_recursion_budget(state_few)
        assert result_few["status"] == "caution"
        assert result_few["recommendations"]["allow_drill_down"] is True

        # Many subtasks left (>3) - should not allow drill-down
        state_many = {
            "node_execution_count": 90,
            "recursion_limit": 150,
            "master_plan": {"subtasks": ["t1", "t2", "t3", "t4", "t5", "t6"]},
            "current_subtask_index": 1,  # 5 remaining
        }
        result_many = calculate_recursion_budget(state_many)
        assert result_many["status"] == "caution"
        assert result_many["recommendations"]["allow_drill_down"] is False


class TestIncrementExecutionCount:
    """Test execution count incrementing."""

    def test_increment_from_zero(self):
        """Test incrementing from 0."""
        state = {}

        result = increment_execution_count(state)

        assert result["node_execution_count"] == 1

    def test_increment_from_existing_count(self):
        """Test incrementing existing count."""
        state = {"node_execution_count": 50}

        result = increment_execution_count(state)

        assert result["node_execution_count"] == 51

    def test_increment_multiple_times(self):
        """Test incrementing multiple times."""
        state = {"node_execution_count": 10}

        for i in range(5):
            result = increment_execution_count(state)
            state["node_execution_count"] = result["node_execution_count"]

        assert state["node_execution_count"] == 15

    def test_increment_does_not_modify_other_state(self):
        """Test that increment only returns execution count."""
        state = {
            "node_execution_count": 5,
            "other_field": "value",
            "master_plan": {},
        }

        result = increment_execution_count(state)

        # Should only return node_execution_count
        assert len(result) == 1
        assert "node_execution_count" in result
        assert "other_field" not in result


class TestLogBudgetStatus:
    """Test budget status logging."""

    def test_log_healthy_status(self, capsys):
        """Test logging healthy status."""
        budget_analysis = {
            "status": "healthy",
            "message": "🟢 HEALTHY: 30.0% used (105 remaining)",
            "current_count": 45,
            "limit": 150,
            "will_exceed": False,
            "remaining_subtasks": 2,
            "avg_per_subtask": 22.5,
            "recommendations": {
                "allow_drill_down": True,
                "allow_plan_revision": True,
                "max_new_subtasks": 5,
            },
        }

        log_budget_status(budget_analysis, context="Test Context")

        captured = capsys.readouterr()
        assert "💰 Recursion Budget (Test Context)" in captured.out
        assert "HEALTHY" in captured.out

    def test_log_warning_status(self, capsys):
        """Test logging warning status."""
        budget_analysis = {
            "status": "warning",
            "message": "🟡 WARNING: 80.0% used (30 remaining)",
            "current_count": 120,
            "limit": 150,
            "will_exceed": True,
            "estimated_total_needed": 200,
            "remaining_subtasks": 1,
            "avg_per_subtask": 120.0,
            "recommendations": {
                "allow_drill_down": False,
                "allow_plan_revision": True,
                "max_new_subtasks": 1,
            },
        }

        log_budget_status(budget_analysis, context="Drill-Down")

        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "Current: 120/150" in captured.out
        assert "Remaining subtasks: 1" in captured.out
        assert "Drill-down DISABLED" in captured.out

    def test_log_critical_status(self, capsys):
        """Test logging critical status."""
        budget_analysis = {
            "status": "critical",
            "message": "🔴 CRITICAL: 93.3% used (10 remaining)",
            "current_count": 140,
            "limit": 150,
            "will_exceed": False,
            "remaining_subtasks": 0,
            "avg_per_subtask": 140.0,
            "recommendations": {
                "allow_drill_down": False,
                "allow_plan_revision": False,
                "max_new_subtasks": 0,
            },
        }

        log_budget_status(budget_analysis, context="Plan Revision")

        captured = capsys.readouterr()
        assert "CRITICAL" in captured.out
        assert "Drill-down DISABLED" in captured.out
        assert "Plan revision DISABLED" in captured.out

    def test_log_will_exceed_warning(self, capsys):
        """Test logging when budget will exceed."""
        budget_analysis = {
            "status": "warning",
            "message": "🟡 WARNING: 70.0% used (45 remaining)",
            "current_count": 105,
            "limit": 150,
            "will_exceed": True,
            "estimated_total_needed": 200,
            "remaining_subtasks": 3,
            "avg_per_subtask": 35.0,
            "recommendations": {
                "allow_drill_down": False,
                "allow_plan_revision": True,
                "max_new_subtasks": 1,
            },
        }

        log_budget_status(budget_analysis)

        captured = capsys.readouterr()
        assert "Estimated total needed: 200" in captured.out
        assert "exceeds limit of 150" in captured.out

    def test_log_limited_new_subtasks(self, capsys):
        """Test logging when new subtasks are limited."""
        budget_analysis = {
            "status": "caution",
            "message": "🟠 CAUTION: 60.0% used (60 remaining)",
            "current_count": 90,
            "limit": 150,
            "will_exceed": False,
            "remaining_subtasks": 2,
            "avg_per_subtask": 30.0,
            "recommendations": {
                "allow_drill_down": True,
                "allow_plan_revision": True,
                "max_new_subtasks": 2,
            },
        }

        log_budget_status(budget_analysis, context="Test")

        captured = capsys.readouterr()
        assert "Max new subtasks limited to: 2" in captured.out
