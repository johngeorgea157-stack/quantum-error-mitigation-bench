"""
Noise Characterisation — Backend Analysis
==========================================
Run process tomography on a target IBM Quantum backend to identify
dominant noise channels (depolarising, T1/T2 relaxation) and document
baseline noise rates per gate type.

Usage:
    python noise_characterisation/characterise_backend.py

References:
    - Temme et al. (2017) — arXiv:1612.02058
    - Qiskit Runtime docs: https://docs.quantum.ibm.com/
"""

# TODO: Implement after completing Day 1-3 theory reading
# Steps:
#   1. Connect to IBM backend via Qiskit Runtime
#   2. Run process tomography on 1- and 2-qubit gates
#   3. Extract noise channel parameters (depol rate, T1, T2)
#   4. Save noise model as JSON to noise_characterisation/data/
#   5. Print summary of dominant noise channels
