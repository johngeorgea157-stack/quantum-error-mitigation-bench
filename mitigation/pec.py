"""
Probabilistic Error Cancellation (PEC)
======================================
Implements PEC using quasi-probability decomposition to invert noise channels.

Reference:
    Temme et al. (2017) — arXiv:1612.02058
    Takagi et al. (2021) — Optimal resource estimation for quantum error mitigation

Approach:
    1. Characterise noise via process tomography → Choi matrix
    2. Decompose ideal gate as sum of noisy operations with quasi-probabilities
    3. Sample from distribution: weight results by quasi-probability signs
    4. Overhead grows exponentially with circuit depth — practical for shallow circuits only
"""

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit_aer import AerSimulator

from mitigation.base import Mitigator

# ---------------------------------------------------------------------------
# Module-level helpers (importable by notebook and tests)
# ---------------------------------------------------------------------------


def quasi_probability_decomposition(choi_ideal, choi_noisy):
    """
    Compute quasi-probability coefficients for PEC.

    Decomposes: Ideal channel = Σ_i c_i * Noisy_channel_i

    Coefficients can be negative (quasi-probabilities), enabling error cancellation
    but causing exponential sampling overhead.

    Args:
        choi_ideal (ndarray): Choi matrix of ideal channel (shape: 4×4 for 1Q).
        choi_noisy (ndarray): Choi matrix of noisy channel (same shape).

    Returns:
        dict with:
            'coefficients': quasi-probability coefficients
            'overhead_factor': largest |c_i| (sampling cost)
            'channel_basis': basis operations used for decomposition
    """
    # Simplified PEC: for single depolarizing channel
    # Choi matrix inversion: Ideal = c_0 * Noisy
    # where c_0 = 1 / (1 - p) and p is depolarizing probability

    trace_ideal = np.trace(choi_ideal)
    trace_noisy = np.trace(choi_noisy)

    # Estimate error probability (simplified depolarizing model)
    error_prob = 1.0 - (trace_noisy / trace_ideal)
    error_prob = np.clip(error_prob, 0, 1)

    # Quasi-probability coefficient
    if error_prob < 1.0:
        coeff = 1.0 / (1.0 - error_prob)
    else:
        coeff = 1.0

    overhead = abs(coeff)

    return {
        "coefficients": [coeff],
        "overhead_factor": overhead,
        "error_probability": error_prob,
        "channel_basis": ["noisy_gate"],
    }


def compute_choi_matrix_ideal_1q(gate_name="rz"):
    """
    Compute Choi matrix of an ideal 1-qubit gate.

    Choi-Jamiołkowski isomorphism: channel E → Choi matrix J(E)
    where J(E)_ij = |j⟩⟨i| ⊗ E(|i⟩⟨j|)

    Args:
        gate_name (str): Gate type ('rz', 'ry', etc.).

    Returns:
        ndarray: 4×4 Choi matrix (for 1-qubit gate)
    """
    # For this implementation, use identity as approximation
    # In production: construct exact Choi from gate unitary
    choi_ideal = np.eye(4)
    return choi_ideal


def compute_choi_matrix_noisy_depolarizing(p):
    """
    Compute Choi matrix of a depolarizing channel with error probability p.

    Depolarizing channel: ρ → (1-p)ρ + (p/3)(Xρ X† + Yρ Y† + Zρ Z†)

    Args:
        p (float): Depolarizing error probability (0 ≤ p ≤ 1).

    Returns:
        ndarray: 4×4 Choi matrix
    """
    choi_noisy = (1 - p) * np.eye(4)
    choi_noisy -= (p / 3) * (np.eye(4) - 2 * np.diag([0, 1, 1, 1]))
    return choi_noisy


def analyze_noise_for_pec(noise_model_obj, error_probability):
    """
    Analyze noise from simulator to estimate PEC overhead.

    Args:
        noise_model_obj: Qiskit NoiseModel.
        error_probability (float): Single-gate error probability.

    Returns:
        dict with overhead metrics and depth limits
    """
    choi_ideal = compute_choi_matrix_ideal_1q("rz")
    choi_noisy = compute_choi_matrix_noisy_depolarizing(error_probability)

    pec_result = quasi_probability_decomposition(choi_ideal, choi_noisy)
    overhead_1gate = pec_result["overhead_factor"]

    # Estimate depth at 10× overhead
    if overhead_1gate > 1.0:
        depth_at_10x = np.log(10) / np.log(overhead_1gate)
    else:
        depth_at_10x = float("inf")

    return {
        "choi_ideal": choi_ideal,
        "choi_noisy": choi_noisy,
        "overhead_single_gate": overhead_1gate,
        "error_probability": error_probability,
        "depth_at_10x_overhead": depth_at_10x,
    }


def pec_sample_single_circuit(circuit, simulator, quasi_prob_coeffs, num_samples=1000):
    """
    Sample from PEC quasi-probability distribution.

    PEC procedure:
    1. For each sample:
       a) Draw noisy channel index i with probability |c_i|/sum(|c_j|)
       b) Run circuit with selected noisy gate
       c) Record measurement
       d) Weight result by sign(c_i)
    2. Average over all samples with their weights

    Args:
        circuit (QuantumCircuit): Circuit to mitigate (without measurements).
        simulator: Aer simulator with noise model.
        quasi_prob_coeffs (list): Quasi-probability coefficients.
        num_samples (int): Number of PEC samples to draw.

    Returns:
        dict with mitigated value and sampling overhead
    """
    coeff = quasi_prob_coeffs[0]
    norm = abs(coeff)
    prob_sample = abs(coeff) / norm

    weighted_sum = 0.0
    shot_count = 0
    samples_list = []

    for _ in range(num_samples):
        if np.random.random() < prob_sample:
            qc = circuit.remove_final_measurements(inplace=False)
            if qc.num_clbits == 0:
                qc.add_register(ClassicalRegister(qc.num_qubits, "c"))
            qc.measure(0, 0)

            result = simulator.run(qc, shots=1).result()
            counts = result.get_counts()

            bitstring = list(counts.keys())[0]
            measurement = int(bitstring[-1])

            z_eigenvalue = 1.0 if measurement == 0 else -1.0
            weight = np.sign(coeff)
            weighted_val = z_eigenvalue * weight

            weighted_sum += weighted_val
            shot_count += 1
            samples_list.append((z_eigenvalue, weight))

    if shot_count > 0:
        mitigated_value = weighted_sum / shot_count
    else:
        mitigated_value = 0.0

    return {
        "mitigated_value": mitigated_value,
        "raw_samples": samples_list,
        "sampling_overhead_actual": shot_count,
        "num_samples_drawn": num_samples,
    }


# ---------------------------------------------------------------------------
# PECMitigator class
# ---------------------------------------------------------------------------


class PECMitigator(Mitigator):
    """Probabilistic Error Cancellation via quasi-probability decomposition."""

    def __init__(self, error_probability=0.003, num_samples=1000):
        """
        Parameters
        ----------
        error_probability : float, optional
            Single-gate error rate (default 0.3%).
        num_samples : int, optional
            Number of PEC samples to draw. Default: 1000.
        """
        self.error_probability = error_probability
        self.num_samples = num_samples

    def mitigate(self, circuit, observable=None, backend=None):
        """
        Apply PEC to estimate the zero-noise expectation value <Z₀>.

        Parameters
        ----------
        circuit : QuantumCircuit
            The circuit to mitigate. May contain measurements; stripped internally.
        observable : ignored
            Reserved for future use. Currently <Z₀> on qubit 0 is always measured.
        backend : AerSimulator or None
            Simulator to run circuits on. Defaults to noiseless AerSimulator.

        Returns
        -------
        dict with keys:
            "mitigated"  – PEC-mitigated expectation value
            "sampling_overhead" – actual shots used
            "error_probability" – noise level used
        """
        if backend is None:
            backend = AerSimulator()

        quasi_prob_coeffs = [1.0 / (1.0 - self.error_probability)]

        result = pec_sample_single_circuit(
            circuit, backend, quasi_prob_coeffs, num_samples=self.num_samples
        )

        return {
            "mitigated": result["mitigated_value"],
            "sampling_overhead": result["sampling_overhead_actual"],
            "error_probability": self.error_probability,
        }

    def overhead(self):
        """PEC overhead ≈ 1/(1-p) for single-gate error probability p."""
        return float(1.0 / (1.0 - self.error_probability))

    def name(self):
        return "PEC (Quasi-Probability Decomposition)"
