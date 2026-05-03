"""
Abstract Mitigator Base Class
==============================
Defines the common interface that all error mitigation methods must implement.
This enables a pluggable design where any mitigator can be swapped in
during benchmarking.

Design:
    - Each mitigator wraps around a Qiskit Estimator/Sampler primitive
    - `mitigate()` takes a circuit + observable and returns a corrected
      expectation value
    - `overhead()` reports the extra circuit evaluations required
"""

from abc import ABC, abstractmethod


class Mitigator(ABC):
    """Abstract base class for all error mitigation methods."""

    @abstractmethod
    def mitigate(self, circuit, observable, backend=None):
        """
        Run the circuit and return a mitigated expectation value.

        Parameters
        ----------
        circuit : QuantumCircuit
            The circuit to execute.
        observable : SparsePauliOp
            The observable to measure.
        backend : IBMBackend or AerSimulator, optional
            The backend to run on.

        Returns
        -------
        float
            The mitigated expectation value.
        """
        pass

    @abstractmethod
    def overhead(self):
        """
        Return the overhead factor for this mitigation method.

        Returns
        -------
        float or str
            Number of extra circuit evaluations relative to a single
            unmitigated run. E.g., 3.0 for ZNE with 3 noise levels.
        """
        pass

    @abstractmethod
    def name(self):
        """Return human-readable name of this mitigator."""
        pass
