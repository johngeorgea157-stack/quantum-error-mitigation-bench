"""
Tests for CDR Mitigator
========================
Validates CDR correctness:
    - Near-Clifford circuit generation
    - Linear regression fit quality
    - Mitigated value closer to exact than raw noisy value
"""

import pytest
from mitigation.cdr import CDRMitigator


class TestCDRMitigator:
    """Test suite for Clifford Data Regression."""

    def test_init_default(self):
        """Default should use 10 training circuits."""
        cdr = CDRMitigator()
        assert cdr.n_training_circuits == 10

    def test_init_custom(self):
        """Custom training circuit count should be stored."""
        cdr = CDRMitigator(n_training_circuits=20)
        assert cdr.n_training_circuits == 20

    def test_overhead(self):
        """Overhead should be n_training + 1."""
        cdr = CDRMitigator(n_training_circuits=10)
        assert cdr.overhead() == 11.0

    def test_name(self):
        """Name should identify the method."""
        cdr = CDRMitigator()
        assert "CDR" in cdr.name()

    def test_no_regression_coefficients_initially(self):
        """Regression coefficients should be None before fitting."""
        cdr = CDRMitigator()
        assert cdr.regression_coefficients is None

    def test_mitigate_not_implemented(self):
        """mitigate() should raise NotImplementedError until implemented."""
        cdr = CDRMitigator()
        with pytest.raises(NotImplementedError):
            cdr.mitigate(None, None)

    # TODO: Add after Day 6 implementation
    # def test_near_clifford_generation(self):
    # def test_regression_fit_quality(self):
    # def test_cdr_corrects_noisy_value(self):
