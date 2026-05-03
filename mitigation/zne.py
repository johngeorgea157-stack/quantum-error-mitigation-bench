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

from mitigation.base import Mitigator


class ZNEMitigator(Mitigator):
    """Zero-Noise Extrapolation via gate folding + Richardson extrapolation."""

    def __init__(self, noise_levels=None):
        """
        Parameters
        ----------
        noise_levels : list of int, optional
            Stretch factors for gate folding. Default: [1, 3, 5].
        """
        self.noise_levels = noise_levels or [1, 3, 5]

    def mitigate(self, circuit, observable, backend=None):
        """
        Apply ZNE to get a mitigated expectation value.

        TODO: Implement after Day 4 (ZNE implementation day)
        Steps:
            1. For each noise level, apply gate folding to circuit
            2. Run each folded circuit on backend
            3. Collect noisy expectation values
            4. Apply Richardson extrapolation to estimate zero-noise value
        """
        raise NotImplementedError("ZNE mitigate() — implement on Day 4")

    def overhead(self):
        """ZNE overhead = number of noise levels evaluated."""
        return float(len(self.noise_levels))

    def name(self):
        return "ZNE (Richardson Extrapolation)"
