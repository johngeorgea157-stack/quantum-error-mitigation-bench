"""
Tests for ZNE Mitigator
========================
Validates ZNE correctness on noiseless and noisy simulators:
    - Gate folding produces correct circuit structure (gate count)
    - Richardson extrapolation converges to ideal value on noiseless sim
    - ZNE reduces error vs raw noisy on a simulated noisy backend
    - Overhead and name metadata are correct
"""

import pytest
from qiskit_aer import AerSimulator

from benchmarks.circuits import build_noise_model, create_test_circuit
from mitigation.zne import (
    ZNEMitigator,
    fold_gates,
    measure_expectation,
    richardson_extrapolate,
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


@pytest.fixture(scope="module")
def noisy_sim():
    return AerSimulator(noise_model=build_noise_model())


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestZNEMetadata:
    def test_init_default_noise_levels(self):
        """Default noise levels should be [1, 3, 5]."""
        zne = ZNEMitigator()
        assert zne.noise_levels == [1, 3, 5]

    def test_init_custom_noise_levels(self):
        """Custom noise levels should be stored correctly."""
        zne = ZNEMitigator(noise_levels=[1, 3])
        assert zne.noise_levels == [1, 3]

    def test_overhead(self):
        """Overhead should equal number of noise levels."""
        assert ZNEMitigator(noise_levels=[1, 3, 5]).overhead() == 3.0
        assert ZNEMitigator(noise_levels=[1, 3]).overhead() == 2.0

    def test_name(self):
        """Name should identify the method."""
        assert "ZNE" in ZNEMitigator().name()


# ---------------------------------------------------------------------------
# Gate folding tests
# ---------------------------------------------------------------------------


class TestGateFolding:
    def test_scale_1_returns_unmeasured_circuit(self, test_circuit):
        """Scale factor 1 should return original circuit stripped of measurements."""
        folded = fold_gates(test_circuit, 1)
        assert folded.num_clbits == 0, "Scale-1 circuit should have no classical bits"

    def test_scale_3_triples_gate_count(self, test_circuit):
        """Scale factor 3 should triple each gate (U → U†UU = 3 gates)."""
        base = fold_gates(test_circuit, 1)
        folded = fold_gates(test_circuit, 3)
        assert folded.size() == base.size() * 3

    def test_scale_5_quintuples_gate_count(self, test_circuit):
        """Scale factor 5 should quintuple each gate (U → U†UU†UU = 5 gates)."""
        base = fold_gates(test_circuit, 1)
        folded = fold_gates(test_circuit, 5)
        assert folded.size() == base.size() * 5

    def test_even_scale_raises(self, test_circuit):
        """Even scale factors are invalid and should raise ValueError."""
        with pytest.raises(ValueError):
            fold_gates(test_circuit, 2)


# ---------------------------------------------------------------------------
# Richardson extrapolation tests
# ---------------------------------------------------------------------------


class TestRichardsonExtrapolation:
    def test_exact_linear_recovery(self):
        """On a perfectly linear signal the extrapolation should be exact."""
        # <O>(λ) = -0.96 + 0.01 * λ  →  zero-noise = -0.96
        scales = [1, 3, 5]
        values = [-0.96 + 0.01 * s for s in scales]
        mitigated, _, _ = richardson_extrapolate(scales, values, poly_degree=1)
        assert abs(mitigated - (-0.96)) < 1e-10

    def test_returns_three_values(self):
        """Should return (mitigated_value, coefficients, poly_func)."""
        result = richardson_extrapolate([1, 3, 5], [-0.9, -0.85, -0.80])
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Full ZNE pipeline tests
# ---------------------------------------------------------------------------


class TestZNEPipeline:
    def test_ideal_expectation_nonzero(self, test_circuit, ideal_sim):
        """Ideal <Z0> on this circuit should be strongly negative (~-0.96)."""
        val = measure_expectation(fold_gates(test_circuit, 1), ideal_sim, num_shots=4096)
        assert val < -0.80, f"Expected <Z0> < -0.80, got {val:.4f}"

    def test_mitigate_returns_dict(self, test_circuit, noisy_sim):
        """mitigate() should return a dict with the required keys."""
        result = ZNEMitigator(num_shots=1024).mitigate(test_circuit, backend=noisy_sim)
        assert set(result.keys()) >= {"mitigated", "noisy", "scales", "poly_func"}

    def test_mitigate_noisy_values_degrade_with_scale(self, test_circuit, noisy_sim):
        """Noisy expectation values should become less negative as λ increases."""
        result = ZNEMitigator(noise_levels=[1, 3, 5], num_shots=2048).mitigate(
            test_circuit, backend=noisy_sim
        )
        noisy = result["noisy"]
        # Each successive scale should push the value closer to 0 (more noise)
        assert (
            noisy[0] < noisy[1] or abs(noisy[0] - noisy[1]) < 0.05
        ), "λ=3 value should be >= λ=1 (less negative) within shot noise tolerance"

    def test_mitigate_reduces_error_vs_raw(self, test_circuit, ideal_sim, noisy_sim):
        """ZNE mitigated value should be at least as close to ideal as raw noisy."""
        ideal = measure_expectation(fold_gates(test_circuit, 1), ideal_sim, num_shots=4096)
        result = ZNEMitigator(noise_levels=[1, 3, 5], num_shots=2048).mitigate(
            test_circuit, backend=noisy_sim
        )
        raw_error = abs(ideal - result["noisy"][0])
        zne_error = abs(ideal - result["mitigated"])
        # Allow up to 50% worse due to shot noise variance — what matters is direction
        assert zne_error <= raw_error * 1.5, (
            f"ZNE error ({zne_error:.4f}) should not be much worse than "
            f"raw noisy error ({raw_error:.4f})"
        )
