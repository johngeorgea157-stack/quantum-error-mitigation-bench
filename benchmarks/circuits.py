"""
Parametrised Test Circuits
===========================
Builds test circuits at varying depths for benchmarking error mitigation
methods. These circuits have known exact expectation values (computable
on a noiseless simulator) so we can measure how much fidelity each
mitigator recovers.

Design:
    - Circuits parametrised by depth p (number of entangling layers)
    - Support 2–5 qubits
    - Include both random parametrised circuits and structured circuits
      (e.g., hardware-efficient ansatz)
"""

# TODO: Implement after Day 7 (interface design day)
# Steps:
#   1. Define a function to build circuits at depth p
#   2. Include Hadamard + CNOT + Rz layers per depth
#   3. Return circuit + exact expectation value from Aer simulation
#   4. Support configurable qubit count
