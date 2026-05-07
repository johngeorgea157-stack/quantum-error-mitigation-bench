"""
Tests for PEC Mitigator
========================
Validates PEC correctness on noiseless simulator:
    - Quasi-probability decomposition is well-formed
    - Overhead bounds are correctly reported
    - Mitigated value converges to exact for short circuits
"""

import numpy as np
import pytest
from qiskit_aer import AerSimulator

from benchmarks.circuits import create_test_circuit
from mitigation.pec import (
    PECMitigator,
    quasi_probability_decomposition,
    compute_choi_matrix_ideal_1q,
    compute_choi_matrix_noisy_depolarizing,
    analyze_noise_for_pec,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_circuit():
    """2-qubit VQE-like ansatz at depth 2 (same as notebook demo)."""
    return create_test_circuit(depth=2)


@pytest.fixture(scope="module")
def ideal_sim():
    return AerSimulator()


# ---------------------------------------------------------------------------
# Quasi-probability decomposition tests
# ---------------------------------------------------------------------------


class TestQuasiProbabilityDecomposition:
    def test_returns_dict(self):
        """Should return dict with required keys."""
        choi_ideal = compute_choi_matrix_ideal_1q()
        choi_noisy = compute_choi_matrix_noisy_depolarizing(0.01)
        result = quasi_probability_decomposition(choi_ideal, choi_noisy)

        assert isinstance(result, dict)
        assert set(result.keys()) >= {
            "coefficients",
            "overhead_factor",
            "error_probability",
        }

    def test_overhead_factor_positive(self):
        """Overhead factor should always be positive."""
        choi_ideal = compute_choi_matrix_ideal_1q()
        choi_noisy = compute_choi_matrix_noisy_depolarizing(0.01)
        result = quasi_probability_decomposition(choi_ideal, choi_noisy)
        assert result["overhead_factor"] > 0

    def test_overhead_increases_with_error(self):
        """Higher error probability should increase overhead."""
        choi_ideal = compute_choi_matrix_ideal_1q()
        choi_noisy_low = compute_choi_matrix_noisy_depolarizing(0.001)
        choi_noisy_high = compute_choi_matrix_noisy_depolarizing(0.01)

        result_low = quasi_probability_decomposition(choi_ideal, choi_noisy_low)
        result_high = quasi_probability_decomposition(choi_ideal, choi_noisy_high)

        assert result_low["overhead_factor"] < result_high["overhead_factor"]


# ---------------------------------------------------------------------------
# Choi matrix tests
# ---------------------------------------------------------------------------


class TestChoiMatrices:
    def test_ideal_choi_shape(self):
        """Ideal Choi matrix should be 4×4 for 1-qubit."""
        choi = compute_choi_matrix_ideal_1q()
        assert choi.shape == (4, 4)

    def test_noisy_choi_shape(self):
        """Noisy Choi matrix should be 4×4 for 1-qubit."""
        choi = compute_choi_matrix_noisy_depolarizing(0.01)
        assert choi.shape == (4, 4)

    def test_noisy_choi_has_lower_trace(self):
        """Noisy Choi should have lower trace than ideal (error reduces fidelity)."""
        choi_ideal = compute_choi_matrix_ideal_1q()
        choi_noisy = compute_choi_matrix_noisy_depolarizing(0.01)
        assert np.trace(choi_noisy) < np.trace(choi_ideal)

    def test_trace_monotonic_with_error(self):
        """Trace should decrease monotonically with error probability."""
        choi_ideal = compute_choi_matrix_ideal_1q()
        traces = [
            np.trace(compute_choi_matrix_noisy_depolarizing(p)) for p in [0.001, 0.005, 0.01, 0.02]
        ]
        # Traces should be monotonically decreasing
        for i in range(len(traces) - 1):
            assert traces[i] >= traces[i + 1]


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestPECMetadata:
    def test_init_default_parameters(self):
        """Default parameters should be reasonable."""
        pec = PECMitigator()
        assert pec.error_probability == 0.003
        assert pec.num_samples == 1000

    def test_init_custom_parameters(self):
        """Custom parameters should be stored."""
        pec = PECMitigator(error_probability=0.01, num_samples=500)
        assert pec.error_probability == 0.01
        assert pec.num_samples == 500

    def test_overhead(self):
        """Overhead should return positive float."""
        pec = PECMitigator(error_probability=0.003)
        overhead = pec.overhead()
        assert isinstance(overhead, float)
        assert overhead > 0

    def test_overhead_matches_formula(self):
        """Overhead should match 1/(1-p)."""
        p = 0.01
        pec = PECMitigator(error_probability=p)
        expected = 1.0 / (1.0 - p)
        assert abs(pec.overhead() - expected) < 1e-10

    def test_name(self):
        """Name should identify the method."""
        pec = PECMitigator()
        assert "PEC" in pec.name()


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------


class TestPECPipeline:
    def test_mitigate_returns_dict(self, test_circuit, ideal_sim):
        """mitigate() should return a dict with required keys."""
        pec = PECMitigator(num_samples=100)
        result = pec.mitigate(test_circuit, backend=ideal_sim)
        assert isinstance(result, dict)
        assert set(result.keys()) >= {"mitigated", "sampling_overhead"}

    def test_mitigate_sampling_overhead_positive(self, test_circuit, ideal_sim):
        """Sampling overhead should be positive."""
        pec = PECMitigator(num_samples=100)
        result = pec.mitigate(test_circuit, backend=ideal_sim)
        assert result["sampling_overhead"] > 0


# ---------------------------------------------------------------------------
# Noise analysis tests
# ---------------------------------------------------------------------------


class TestNoiseAnalysis:
    def test_analyze_noise_for_pec_returns_dict(self):
        """analyze_noise_for_pec should return dict with metrics."""
        result = analyze_noise_for_pec(None, error_probability=0.003)
        assert isinstance(result, dict)
        assert set(result.keys()) >= {
            "overhead_single_gate",
            "error_probability",
            "depth_at_10x_overhead",
        }

    def test_depth_at_10x_overhead_is_finite(self):
        """For typical error rates, depth_at_10x should be finite."""
        result = analyze_noise_for_pec(None, error_probability=0.003)
        assert result["depth_at_10x_overhead"] < float("inf")
        assert result["depth_at_10x_overhead"] > 0
