"""
Tests for PEC Mitigator
========================
Validates PEC correctness on noiseless simulator:
    - Quasi-probability decomposition is well-formed
    - Overhead bounds are correctly reported
    - Mitigated value converges to exact for short circuits
"""

import pytest
from mitigation.pec import PECMitigator


class TestPECMitigator:
    """Test suite for Probabilistic Error Cancellation."""

    def test_init_default(self):
        """Default init should have no noise model."""
        pec = PECMitigator()
        assert pec.noise_model is None

    def test_init_with_noise_model(self):
        """Custom noise model should be stored."""
        model = {"cx": {"depol_rate": 0.01}}
        pec = PECMitigator(noise_model=model)
        assert pec.noise_model == model

    def test_overhead_is_exponential(self):
        """Overhead should indicate exponential scaling."""
        pec = PECMitigator()
        overhead = pec.overhead()
        assert "e^" in str(overhead) or "exp" in str(overhead).lower()

    def test_name(self):
        """Name should identify the method."""
        pec = PECMitigator()
        assert "PEC" in pec.name()

    def test_mitigate_not_implemented(self):
        """mitigate() should raise NotImplementedError until implemented."""
        pec = PECMitigator()
        with pytest.raises(NotImplementedError):
            pec.mitigate(None, None)

    # TODO: Add after Day 5 implementation
    # def test_quasi_prob_decomposition_valid(self):
    # def test_pec_exact_on_noiseless(self):
    # def test_pec_overhead_grows_with_depth(self):
