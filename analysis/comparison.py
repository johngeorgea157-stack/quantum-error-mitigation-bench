"""
Cross-Method Comparison
========================
Answers the key questions:
    - When does ZNE beat PEC?
    - When does CDR win?
    - At what depth does each method break down?

Functions:
    - compare_methods()     — returns ranking table per depth
    - find_breakpoints()    — identifies depth where method fails
    - overhead_vs_fidelity() — plots the trade-off curve
"""

# TODO: Implement after Day 10 (comparison + failure analysis day)
# Steps:
#   1. Load statistical summary from statistics.py
#   2. For each depth, rank methods by mitigated fidelity
#   3. Identify crossover points (where method A beats method B)
#   4. Document failure cases (where mitigated is worse than raw)
#   5. Return comparison DataFrame
