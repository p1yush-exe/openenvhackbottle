"""
Unit tests for ClinicalBench graders.

Run with:
    pytest tests/ -v
"""

import pytest
from clinical_bench.server.sandbox import ExecutionResult
from clinical_bench.server.tasks.clinical_calc import ClinicalCalcTask
from clinical_bench.server.tasks.biostat_power import BiostatPowerTask
from clinical_bench.server.tasks.biocoder import BiocoderTask


class TestClinicalCalcGrader:
    """Test clinical calculator grading logic."""
    
    @pytest.fixture
    def task(self):
        return ClinicalCalcTask(data_path="./clinical_bench/data")
    
    def test_exact_match_gives_full_reward(self, task):
        """Test that exact match within bounds gives 1.0 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        result = ExecutionResult(
            stdout="25.0",
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 1.0
    
    def test_within_bounds_gives_full_reward(self, task):
        """Test that answer within [lower, upper] gives 1.0."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.0,
            "Upper Limit": 26.0
        }
        result = ExecutionResult(
            stdout="24.5",
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 1.0
    
    def test_close_answer_gives_partial_credit(self, task):
        """Test that close answer gives 0.5 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        # Answer slightly outside bounds but within 2× tolerance
        result = ExecutionResult(
            stdout="26.0",
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.5
    
    def test_wrong_answer_gives_minimal_reward(self, task):
        """Test that wrong answer gives 0.3 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        result = ExecutionResult(
            stdout="50.0",  # Way off
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.3
    
    def test_syntax_error_gives_tiny_reward(self, task):
        """Test that syntax error gives 0.1 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        result = ExecutionResult(
            stdout="",
            stderr="",
            timed_out=False,
            syntax_error="SyntaxError on line 1: invalid syntax"
        )
        reward = task.grade(item, result)
        assert reward == 0.1
    
    def test_timeout_gives_zero_reward(self, task):
        """Test that timeout gives 0.0 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        result = ExecutionResult(
            stdout="",
            stderr="",
            timed_out=True,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.0
    
    def test_no_output_gives_zero_reward(self, task):
        """Test that no output gives 0.0 reward."""
        item = {
            "Ground Truth Answer": 25.0,
            "Lower Limit": 24.5,
            "Upper Limit": 25.5
        }
        result = ExecutionResult(
            stdout="",
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.0


class TestBiostatPowerGrader:
    """Test biostat power grading logic."""
    
    @pytest.fixture
    def task(self):
        return BiostatPowerTask(data_path="./clinical_bench/data")
    
    def test_exact_sample_size_match(self, task):
        """Test exact sample size match gives 1.0."""
        item = {
            "estimate_target": "size",
            "answer": 100
        }
        result = ExecutionResult(
            stdout="100",
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 1.0
    
    def test_sample_size_within_10_percent(self, task):
        """Test sample size within 10% gives 0.5."""
        item = {
            "estimate_target": "size",
            "answer": 100
        }
        result = ExecutionResult(
            stdout="108",  # 8% off
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.5
    
    def test_power_exact_match(self, task):
        """Test power within ±1% gives 1.0."""
        item = {
            "estimate_target": "power",
            "answer": 0.80
        }
        result = ExecutionResult(
            stdout="0.802",  # Within 1%
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 1.0
    
    def test_power_partial_credit(self, task):
        """Test power within ±10% gives 0.5."""
        item = {
            "estimate_target": "power",
            "answer": 0.80
        }
        result = ExecutionResult(
            stdout="0.85",  # 6.25% off
            stderr="",
            timed_out=False,
            syntax_error=None
        )
        reward = task.grade(item, result)
        assert reward == 0.5
    
    def test_syntax_error(self, task):
        """Test syntax error gives 0.1."""
        item = {
            "estimate_target": "size",
            "answer": 100
        }
        result = ExecutionResult(
            stdout="",
            stderr="",
            timed_out=False,
            syntax_error="SyntaxError"
        )
        reward = task.grade(item, result)
        assert reward == 0.1


class TestBiocoderGrader:
    """Test biocoder grading logic (token overlap)."""
    
    @pytest.fixture
    def task(self):
        return BiocoderTask(data_path="./clinical_bench/data")
    
    def test_token_overlap_calculation(self):
        """Test token overlap function."""
        from clinical_bench.server.tasks.biocoder import _token_overlap
        
        # Exact match
        assert _token_overlap("hello world", "hello world") == 1.0
        
        # Partial overlap
        overlap = _token_overlap("hello world foo", "hello world bar")
        assert 0.5 < overlap < 1.0  # 2 of 4 unique tokens match
        
        # No overlap
        assert _token_overlap("foo bar", "baz qux") == 0.0
        
        # Empty strings
        assert _token_overlap("", "") == 1.0
        assert _token_overlap("foo", "") == 0.0


class TestSandbox:
    """Test sandboxed code execution."""
    
    def test_simple_execution(self):
        """Test basic code execution."""
        from clinical_bench.server.sandbox import run_code
        
        code = "print('hello')"
        result = run_code(code)
        
        assert result.stdout.strip() == "hello"
        assert not result.timed_out
        assert result.syntax_error is None
    
    def test_syntax_error_detection(self):
        """Test syntax error detection."""
        from clinical_bench.server.sandbox import run_code
        
        code = "print 'hello'"  # Python 3 syntax error
        result = run_code(code)
        
        assert result.syntax_error is not None
        assert "SyntaxError" in result.syntax_error
    
    def test_runtime_error_captured(self):
        """Test runtime errors are captured in stderr."""
        from clinical_bench.server.sandbox import run_code
        
        code = "x = 1 / 0"  # Division by zero
        result = run_code(code)
        
        assert "ZeroDivisionError" in result.stderr or "division by zero" in result.stderr.lower()
    
    def test_timeout_works(self):
        """Test timeout mechanism."""
        from clinical_bench.server.sandbox import run_code
        
        code = """
import time
time.sleep(100)
print('done')
"""
        result = run_code(code, timeout=1)
        
        assert result.timed_out
        assert result.stdout == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
