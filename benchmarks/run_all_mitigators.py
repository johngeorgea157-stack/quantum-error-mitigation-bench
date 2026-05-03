"""
Run All Mitigators
===================
Master benchmarking script that runs all three mitigation methods
(ZNE, PEC, CDR) across multiple circuit depths on real IBM hardware.
Collects raw + mitigated expectation values and saves results.

Usage:
    python benchmarks/run_all_mitigators.py

Output:
    Saves results to results/raw_data/ as JSON files.
    Updates results/metrics.csv with summary statistics.

Note:
    This script requires an active IBM Quantum account token.
    It is EXCLUDED from CI — run manually.
"""

# TODO: Implement after Day 8 (hardware runs)
# Steps:
#   1. Load noise model from noise_characterisation/data/
#   2. Build test circuits at depths p=1,2,3,4,5
#   3. For each circuit depth:
#       a. Run raw (unmitigated) on IBM backend
#       b. Run ZNEMitigator
#       c. Run PECMitigator
#       d. Run CDRMitigator
#   4. Repeat 5+ times for statistical confidence
#   5. Save all results to results/raw_data/
#   6. Print summary table
