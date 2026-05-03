"""
Mitigation Package
==================
Pluggable quantum error mitigation methods.

Exports:
    - Mitigator      (abstract base class)
    - ZNEMitigator   (Zero-Noise Extrapolation)
    - PECMitigator   (Probabilistic Error Cancellation)
    - CDRMitigator   (Clifford Data Regression)
"""

from mitigation.base import Mitigator  # noqa: F401
from mitigation.zne import ZNEMitigator  # noqa: F401
from mitigation.pec import PECMitigator  # noqa: F401
from mitigation.cdr import CDRMitigator  # noqa: F401

__all__ = ["Mitigator", "ZNEMitigator", "PECMitigator", "CDRMitigator"]
