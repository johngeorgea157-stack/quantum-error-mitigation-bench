"""
Tests for ZNE Mitigator
========================
Validates ZNE correctness on noiseless simulator:
    - Gate folding produces correct circuit structure
    - Richardson extrapolation converges to exact value
    - Overhead matches expected noise level count
"""

import pytest
from mitigation.zne import ZNEMitigator


class TestZNEMitigator:
    """Test suite for Zero-Noise Extrapolation."""

    def test_init_default_noise_levels(self):
        """Default noise levels should be [1, 3, 5]."""
        zne = ZNEMitigator()
        assert zne.noise_levels == [1, 3, 5]

    def test_init_custom_noise_levels(self):
        """Custom noise levels should be stored correctly."""
        zne = ZNEMitigator(noise_levels=[1, 2, 3, 4])
        assert zne.noise_levels == [1, 2, 3, 4]

    def test_overhead(self):
        """Overhead should equal number of noise levels."""
        zne = ZNEMitigator(noise_levels=[1, 3, 5])
        assert zne.overhead() == 3.0

    def test_name(self):
        """Name should identify the method."""
        zne = ZNEMitigator()
        assert "ZNE" in zne.name()

    def test_mitigate_not_implemented(self):
        """mitigate() should raise NotImplementedError until implemented."""
        zne = ZNEMitigator()
        with pytest.raises(NotImplementedError):
            zne.mitigate(None, None)

    # TODO: Add after Day 4 implementation
    # def test_gate_folding_circuit_structure(self):
    # def test_richardson_extrapolation_exact_on_noiseless(self):
    # def test_zne_reduces_error_on_noisy_simulator(self):
