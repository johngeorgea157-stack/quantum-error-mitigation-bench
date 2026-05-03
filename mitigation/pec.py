"""
Probabilistic Error Cancellation (PEC)
=======================================
Implements PEC using quasi-probability decomposition of noisy gates
into ideal operations. Requires characterised noise model from
process tomography.

Reference:
    Temme et al. (2017) — arXiv:1612.02058

Warning:
    PEC has EXPONENTIAL sampling overhead in circuit depth.
    Practical only for short circuits with well-characterised noise.
"""

from mitigation.base import Mitigator


class PECMitigator(Mitigator):
    """Probabilistic Error Cancellation via quasi-probability decomposition."""

    def __init__(self, noise_model=None):
        """
        Parameters
        ----------
        noise_model : dict, optional
            Characterised noise model from process tomography.
            Maps gate names to noise channel parameters.
        """
        self.noise_model = noise_model

    def mitigate(self, circuit, observable, backend=None):
        """
        Apply PEC to get a mitigated expectation value.

        TODO: Implement after Day 5 (PEC implementation day)
        Steps:
            1. Decompose each noisy gate into ideal + noise-inverse via
               quasi-probability representation
            2. Sample from the quasi-probability distribution
            3. Average over many samples (high overhead!)
            4. Return corrected expectation value
        """
        raise NotImplementedError("PEC mitigate() — implement on Day 5")

    def overhead(self):
        """PEC overhead is exponential in circuit depth — document this."""
        return "O(e^(n*gamma))"  # gamma = 1-norm of quasi-prob representation

    def name(self):
        return "PEC (Quasi-Probability Decomposition)"
