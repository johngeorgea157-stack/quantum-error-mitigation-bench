"""
Baseline Benchmark — Raw Fidelity
==================================
Run parametrised circuits at varying depths (p=1, 2, 3, ...) on real IBM
hardware WITHOUT any error mitigation. This establishes the raw fidelity
baseline that all mitigation methods will be compared against.

Usage:
    python noise_characterisation/baseline_benchmark.py

Output:
    Saves raw expectation values to noise_characterisation/data/baseline.json
"""

# TODO: Implement after setting up Qiskit Runtime (Day 2)
# Steps:
#   1. Define test circuits at depths p=1,2,3,4,5
#   2. Compute exact (noiseless) expectation values via Aer simulator
#   3. Run same circuits on real IBM backend
#   4. Record raw (unmitigated) expectation values
#   5. Save results to data/baseline.json
#   6. Print raw fidelity table: depth vs raw error
