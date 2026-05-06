"""
Zero-Noise Extrapolation (ZNE)
==============================
Implements ZNE using gate folding to artificially amplify noise,
then applies Richardson extrapolation to estimate the zero-noise limit.

Reference:
    Temme et al. (2017) — arXiv:1612.02058
    ZNE unified approach — arXiv:2011.01157

Approach:
    1. Run circuit at noise levels c=1, c=3, c=5 (via gate folding)
    2. Fit polynomial / Richardson extrapolation
    3. Extrapolate to c=0 (zero noise)
"""

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit_aer import AerSimulator

from mitigation.base import Mitigator

# ---------------------------------------------------------------------------
# Module-level helpers (importable by notebook and tests)
# ---------------------------------------------------------------------------


def fold_gates(circuit, scale_factor):
    """
    Fold gates in a circuit to scale noise by `scale_factor`.

    For scale_factor λ:
    - λ = 1: no folding  (return original circuit without measurements)
    - λ = 3: replace each gate U with U†UU
    - λ = 5: replace each gate U with U†UU†UU

    Args:
        circuit (QuantumCircuit): Input circuit (may contain measurements).
        scale_factor (int): Noise scaling factor — must be a positive odd integer.

    Returns:
        QuantumCircuit: Folded circuit without final measurements.
    """
    if scale_factor == 1:
        return circuit.remove_final_measurements(inplace=False)

    if scale_factor % 2 == 0:
        raise ValueError("scale_factor must be a positive odd integer (1, 3, 5, …)")

    num_folds = (scale_factor - 1) // 2

    # Strip measurements from the original circuit first
    qc_no_measure = circuit.remove_final_measurements(inplace=False)

    folded = QuantumCircuit(circuit.num_qubits)

    for instruction in qc_no_measure.data:
        # Use named attributes — compatible with Qiskit ≥ 1.2 (avoids DeprecationWarning)
        gate = instruction.operation
        qubits = instruction.qubits

        # Original gate
        folded.append(gate, qubits)

        # Folding pairs: gate†, gate (repeated num_folds times)
        for _ in range(num_folds):
            folded.append(gate.inverse(), qubits)
            folded.append(gate, qubits)

    return folded


def measure_expectation(circuit, simulator, num_shots=1024):
    """
    Measure the expectation value <Z₀> on qubit 0.

    Args:
        circuit (QuantumCircuit): Circuit without measurements (from fold_gates).
        simulator: Aer simulator instance.
        num_shots (int): Number of measurement shots.

    Returns:
        float: <Z₀> = P(qubit 0 = 0) − P(qubit 0 = 1)
    """
    # Ensure we have no stale measurements
    qc = circuit.remove_final_measurements(inplace=False)

    # Add classical register if absent
    if qc.num_clbits == 0:
        qc.add_register(ClassicalRegister(qc.num_qubits, "c"))

    # Measure only qubit 0 into classical bit 0
    qc.measure(0, 0)

    result = simulator.run(qc, shots=num_shots).result()
    counts = result.get_counts()

    c0 = c1 = 0
    for bitstring, count in counts.items():
        # Qiskit uses little-endian order: rightmost bit = qubit 0
        if int(bitstring[-1]) == 0:
            c0 += count
        else:
            c1 += count

    p0 = c0 / num_shots
    p1 = c1 / num_shots
    return p0 - p1


def richardson_extrapolate(scales, values, poly_degree=2):
    """
    Fit a polynomial to (scale, expectation) pairs and extrapolate to scale=0.

    Assumes: <O>(λ) = a₀ + a₁λ + a₂λ² + …

    Args:
        scales (list[int]):  Noise scale factors [λ₁, λ₂, λ₃, …].
        values (list[float]): Measured expectation values at each scale.
        poly_degree (int): Polynomial degree (default 2).

    Returns:
        tuple: (mitigated_value, coefficients, poly_func)
    """
    scales = np.array(scales, dtype=float)
    values = np.array(values, dtype=float)

    coeffs = np.polyfit(scales, values, poly_degree)
    poly_func = np.poly1d(coeffs)

    # Zero-noise estimate = polynomial evaluated at λ = 0
    mitigated_value = float(poly_func(0))
    return mitigated_value, coeffs, poly_func


# ---------------------------------------------------------------------------
# ZNEMitigator class
# ---------------------------------------------------------------------------


class ZNEMitigator(Mitigator):
    """Zero-Noise Extrapolation via gate folding + Richardson extrapolation."""

    def __init__(self, noise_levels=None, num_shots=1024, poly_degree=2):
        """
        Parameters
        ----------
        noise_levels : list of int, optional
            Odd-integer stretch factors for gate folding. Default: [1, 3, 5].
        num_shots : int, optional
            Number of shots per noise level. Default: 1024.
        poly_degree : int, optional
            Degree of the Richardson polynomial fit. Default: 2.
        """
        self.noise_levels = noise_levels or [1, 3, 5]
        self.num_shots = num_shots
        self.poly_degree = poly_degree

    def mitigate(self, circuit, observable=None, backend=None):
        """
        Apply ZNE to estimate the zero-noise expectation value <Z₀>.

        Parameters
        ----------
        circuit : QuantumCircuit
            The circuit to mitigate.  May contain measurements; they are
            stripped internally.
        observable : ignored
            Reserved for future use (multi-observable support).  Currently
            <Z₀> on qubit 0 is always measured.
        backend : AerSimulator or None
            Simulator to run circuits on.  Defaults to a noiseless
            AerSimulator (useful for unit-testing).

        Returns
        -------
        dict with keys:
            "mitigated"  – ZNE-extrapolated expectation value
            "noisy"      – list of raw noisy values at each noise level
            "scales"     – noise scale factors used
            "poly_func"  – fitted polynomial (callable)
        """
        if backend is None:
            backend = AerSimulator()

        noisy_values = []
        for scale in self.noise_levels:
            folded = fold_gates(circuit, scale)
            exp_val = measure_expectation(folded, backend, num_shots=self.num_shots)
            noisy_values.append(exp_val)

        mitigated, coeffs, poly_func = richardson_extrapolate(
            self.noise_levels, noisy_values, poly_degree=self.poly_degree
        )

        return {
            "mitigated": mitigated,
            "noisy": noisy_values,
            "scales": list(self.noise_levels),
            "poly_func": poly_func,
        }

    def overhead(self):
        """ZNE overhead = number of noise levels evaluated."""
        return float(len(self.noise_levels))

    def name(self):
        return "ZNE (Richardson Extrapolation)"
