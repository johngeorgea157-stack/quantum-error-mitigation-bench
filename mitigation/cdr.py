"""
Clifford Data Regression (CDR)
===============================
Implements CDR by generating near-Clifford training circuits that can
be exactly simulated classically, running them on noisy hardware, and
fitting a linear regression from noisy → exact expectation values.
This learned correction is then applied to the target (non-Clifford) circuit.

Reference:
    Czarnik et al. (2021) — arXiv:2005.10189

Approach:
    1. Generate k near-Clifford circuits (replace non-Clifford gates
       with nearest Clifford)
    2. Simulate exactly (classical) to get ideal expectation values
    3. Run on noisy hardware to get noisy expectation values
    4. Fit: ideal = a * noisy + b  (linear regression)
    5. Apply correction to target circuit's noisy result
"""

from mitigation.base import Mitigator


class CDRMitigator(Mitigator):
    """Clifford Data Regression — learns noise correction from simulable circuits."""

    def __init__(self, n_training_circuits=10):
        """
        Parameters
        ----------
        n_training_circuits : int
            Number of near-Clifford training circuits to generate.
        """
        self.n_training_circuits = n_training_circuits
        self.regression_coefficients = None  # (a, b) from fit

    def mitigate(self, circuit, observable, backend=None):
        """
        Apply CDR to get a mitigated expectation value.

        TODO: Implement after Day 6 (CDR implementation day)
        Steps:
            1. Generate near-Clifford variants of the target circuit
            2. Simulate each exactly (Clifford simulator)
            3. Run each on noisy backend
            4. Fit linear regression: exact = a * noisy + b
            5. Apply correction: mitigated = a * noisy_target + b
        """
        raise NotImplementedError("CDR mitigate() — implement on Day 6")

    def overhead(self):
        """CDR overhead = n_training_circuits + 1 (the target circuit)."""
        return float(self.n_training_circuits + 1)

    def name(self):
        return "CDR (Clifford Data Regression)"
