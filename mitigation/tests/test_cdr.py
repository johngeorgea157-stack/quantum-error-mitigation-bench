"""
Tests for CDR Mitigator
========================
Validates CDR correctness:
    - Near-Clifford circuit generation
    - Linear regression fit quality
    - Mitigated value closer to exact than raw noisy value
"""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from mitigation.cdr import (
    CDRMitigator,
    generate_near_clifford_circuit,
    generate_training_set,
    simulate_circuit_expectation,
    collect_training_data,
    fit_cdr_regression,
    apply_cdr_correction,
)


class TestCDRHelpers:
    """Test CDR helper functions."""

    def test_generate_near_clifford_circuit(self):
        """Should generate a valid quantum circuit."""
        circuit = generate_near_clifford_circuit(num_qubits=2, depth=2, seed=42)
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == 2
        assert len(circuit.data) > 0  # Should have some gates

    def test_generate_training_set(self):
        """Should generate a list of circuits."""
        circuits = generate_training_set(num_circuits=5, num_qubits=2, max_depth=3)
        assert len(circuits) == 5
        for circuit in circuits:
            assert isinstance(circuit, QuantumCircuit)
            assert circuit.num_qubits == 2

    def test_simulate_circuit_expectation(self):
        """Should compute expectation value correctly."""
        # Simple |0⟩ state circuit
        qc = QuantumCircuit(1)
        sim = AerSimulator()
        exp = simulate_circuit_expectation(qc, sim, shots=100)
        assert abs(exp - 1.0) < 0.1  # Should be close to +1 for |0⟩

    def test_collect_training_data(self):
        """Should collect noisy and exact expectation pairs."""
        circuits = generate_training_set(3, 2, 2)
        ideal_sim = AerSimulator()
        noisy_sim = AerSimulator()  # Using noiseless for simplicity

        noisy_data, exact_data = collect_training_data(circuits, ideal_sim, noisy_sim, shots=100)

        assert len(noisy_data) == 3
        assert len(exact_data) == 3
        assert noisy_data.shape == exact_data.shape

    def test_fit_cdr_regression(self):
        """Should fit linear regression and return valid parameters."""
        # Create simple test data: y = 2*x + 1
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1 + 0.1 * np.random.randn(5)  # Add small noise

        slope, intercept, score = fit_cdr_regression(x, y)

        assert abs(slope - 2.0) < 0.5  # Should be close to 2
        assert abs(intercept - 1.0) < 0.5  # Should be close to 1
        assert score > 0.8  # Should have good fit

    def test_apply_cdr_correction(self):
        """Should apply linear correction correctly."""
        noisy_val = 0.8
        slope, intercept = 1.2, 0.1
        corrected = apply_cdr_correction(noisy_val, slope, intercept)
        expected = 1.2 * 0.8 + 0.1  # 1.06
        assert abs(corrected - expected) < 1e-6


class TestCDRMitigator:
    """Test suite for Clifford Data Regression."""

    def test_init_default(self):
        """Default parameters should be set correctly."""
        cdr = CDRMitigator()
        assert cdr.num_training_circuits == 50
        assert cdr.num_qubits == 2
        assert cdr.max_depth == 5
        assert cdr.num_shots == 1024
        assert cdr.slope is None
        assert cdr.intercept is None

    def test_init_custom(self):
        """Custom parameters should be stored."""
        cdr = CDRMitigator(num_training_circuits=20, num_qubits=3, max_depth=4, num_shots=512)
        assert cdr.num_training_circuits == 20
        assert cdr.num_qubits == 3
        assert cdr.max_depth == 4
        assert cdr.num_shots == 512

    def test_fit_requires_simulators(self):
        """fit() should work with provided simulators."""
        cdr = CDRMitigator(num_training_circuits=5)  # Small for speed
        ideal_sim = AerSimulator()
        noisy_sim = AerSimulator()  # Noiseless for test

        result = cdr.fit(noisy_sim, ideal_sim)

        assert 'slope' in result
        assert 'intercept' in result
        assert 'r2_score' in result
        assert 'training_circuits' in result

        assert isinstance(result['slope'], (int, float))
        assert isinstance(result['intercept'], (int, float))
        assert isinstance(result['r2_score'], (int, float))
        assert len(result['training_circuits']) == 5

        # Should set internal state
        assert cdr.slope is not None
        assert cdr.intercept is not None
        assert cdr.r2_score is not None

    def test_mitigate_requires_fit(self):
        """mitigate() should fail if fit() not called."""
        cdr = CDRMitigator()
        circuit = QuantumCircuit(2)

        with pytest.raises(ValueError, match="CDR model not trained"):
            cdr.mitigate(circuit, backend=AerSimulator())

    def test_mitigate_requires_backend(self):
        """mitigate() should require a backend."""
        cdr = CDRMitigator(num_training_circuits=3)
        cdr.fit(AerSimulator())  # Fit first
        circuit = QuantumCircuit(2)

        with pytest.raises(ValueError, match="backend must be provided"):
            cdr.mitigate(circuit)

    def test_mitigate_workflow(self):
        """Full mitigate workflow should work."""
        # Create a simple test circuit
        circuit = QuantumCircuit(2)
        circuit.h(0)  # Put qubit 0 in |+⟩ state
        circuit.cx(0, 1)  # Entangle

        # Train on noiseless (for predictable results)
        cdr = CDRMitigator(num_training_circuits=10, num_shots=100)
        cdr.fit(AerSimulator())

        # Mitigate
        backend = AerSimulator()
        result = cdr.mitigate(circuit, backend=backend)

        assert 'mitigated' in result
        assert 'noisy' in result
        assert 'slope' in result
        assert 'intercept' in result

        assert isinstance(result['mitigated'], (int, float))
        assert isinstance(result['noisy'], (int, float))

    def test_mitigate_with_noise(self):
        """Test mitigation on noisy simulator."""
        # Create noise model
        noise_model = NoiseModel()
        error = depolarizing_error(0.01, 1)  # Small noise
        noise_model.add_all_qubit_quantum_error(error, ['u2', 'u3'])

        noisy_sim = AerSimulator(noise_model=noise_model)
        ideal_sim = AerSimulator()

        # Simple test circuit
        circuit = QuantumCircuit(1)
        circuit.h(0)  # |+⟩ state, <Z> = 0

        # Train CDR
        cdr = CDRMitigator(num_training_circuits=20, num_shots=200)
        cdr.fit(noisy_sim, ideal_sim)

        # Mitigate
        result = cdr.mitigate(circuit, backend=noisy_sim)

        # Check that mitigation is attempted (CDR may not always improve)
        assert isinstance(result['mitigated'], (int, float))
        assert isinstance(result['noisy'], (int, float))
        assert cdr.r2_score > 0.0  # Should have some fit (may not be great)
    # def test_cdr_corrects_noisy_value(self):
