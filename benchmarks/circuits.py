"""
Parametrised Test Circuits
===========================
Builds test circuits at varying depths for benchmarking error mitigation
methods. These circuits have known exact expectation values (computable
on a noiseless simulator) so we can measure how much fidelity each
mitigator recovers.

Design:
    - Circuits parametrised by depth p (number of entangling layers)
    - 2-qubit hardware-efficient ansatz (X + RY + CNOT)
    - Strong Z bias on qubit 0 (ideal <Z0> ≈ -0.96) for clear ZNE signal

Day 4 (ZNE): create_test_circuit() and build_noise_model() implemented.
Day 7 (Interface): extended to multi-qubit / configurable ansatz families.
"""

from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel, depolarizing_error


def create_test_circuit(depth=2):
    """
    Create a simple 2-qubit VQE-like ansatz circuit with a strong |1⟩ bias.

    The circuit applies:
      - X gate on qubit 0  → puts it in |1⟩ (Z = -1 bias)
      - `depth` layers of small RY rotations + CNOT entangling
      - Final small RY to break symmetry

    Ideal <Z0> ≈ -0.96 (strong bias toward |1⟩, slight perturbation from
    RY rotations).  This gives ZNE a non-trivial but recoverable signal.

    Parameters
    ----------
    depth : int
        Number of RY + CNOT ansatz layers (default 2).

    Returns
    -------
    QuantumCircuit
        2-qubit circuit with measurements on all qubits.
    """
    qc = QuantumCircuit(2, name=f"test_circuit_depth_{depth}")

    # Initialise qubit 0 in |1⟩ — strong Z = -1 bias
    qc.x(0)

    for _ in range(depth):
        # Small RY rotations: ~98% of state stays along Z axis
        qc.ry(0.1, 0)
        qc.ry(0.05, 1)
        # Single CNOT adds entanglement without fully mixing
        qc.cx(0, 1)

    # Final small RY to slightly break symmetry
    qc.ry(0.15, 0)

    qc.measure_all()
    return qc


def build_noise_model(error_1q=0.003, error_2q=0.015):
    """
    Build a depolarising noise model that approximates IBM hardware gate errors.

    Parameters
    ----------
    error_1q : float
        Depolarising error rate per single-qubit gate (default 0.3%).
    error_2q : float
        Depolarising error rate per two-qubit gate / CNOT (default 1.5%).

    Returns
    -------
    NoiseModel
        Qiskit Aer noise model ready for use with AerSimulator.
    """
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(error_1q, 1), ["u2", "u3"])
    nm.add_all_qubit_quantum_error(depolarizing_error(error_2q, 2), ["cx"])
    return nm
