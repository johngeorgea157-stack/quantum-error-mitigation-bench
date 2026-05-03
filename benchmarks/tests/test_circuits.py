"""
Tests for Benchmark Circuits
==============================
Validates circuit structure:
    - Correct qubit count
    - Depth scales with parameter p
    - Circuits are valid Qiskit QuantumCircuit objects
"""

import pytest  # noqa: F401

# TODO: Uncomment and implement after circuits.py is built
# from benchmarks.circuits import build_test_circuit


class TestBenchmarkCircuits:
    """Test suite for parametrised benchmark circuits."""

    def test_placeholder(self):
        """Placeholder — replace with real tests after Day 7."""
        assert True

    # TODO: Add after Day 7 implementation
    # def test_circuit_qubit_count(self):
    #     """Circuit should have the requested number of qubits."""
    #     qc = build_test_circuit(n_qubits=3, depth=2)
    #     assert qc.num_qubits == 3

    # def test_circuit_depth_scales(self):
    #     """Deeper circuits should have more gates."""
    #     qc1 = build_test_circuit(n_qubits=3, depth=1)
    #     qc2 = build_test_circuit(n_qubits=3, depth=3)
    #     assert qc2.depth() > qc1.depth()

    # def test_circuit_is_valid(self):
    #     """Should return a valid QuantumCircuit."""
    #     from qiskit import QuantumCircuit
    #     qc = build_test_circuit(n_qubits=2, depth=1)
    #     assert isinstance(qc, QuantumCircuit)
