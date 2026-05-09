"""
Clifford Data Regression (CDR)
==============================
Implements CDR by training on near-Clifford circuits to learn
a linear correction mapping from noisy to exact expectation values.

Reference:
    Czarnik et al. (2021) — arXiv:2005.10189
    "Error mitigation for near-term quantum computing
     via Clifford data regression"

Approach:
    1. Generate near-Clifford training circuits
    2. Collect (noisy, exact) expectation value pairs
    3. Fit linear regression: exact = a * noisy + b
    4. Apply correction to target circuits
"""

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit_aer import AerSimulator
from sklearn.linear_model import LinearRegression

from mitigation.base import Mitigator

# ---------------------------------------------------------------------------
# Module-level helpers (importable by notebook and tests)
# ---------------------------------------------------------------------------


def generate_near_clifford_circuit(num_qubits=2, depth=3, seed=None):
    """
    Generate a near-Clifford circuit for CDR training.

    Args:
        num_qubits (int): Number of qubits
        depth (int): Circuit depth (number of layers)
        seed (int): Random seed for reproducibility

    Returns:
        QuantumCircuit: Near-Clifford circuit
    """
    if seed is not None:
        np.random.seed(seed)

    qc = QuantumCircuit(num_qubits, name=f"near_clifford_{num_qubits}q_d{depth}")

    clifford_gates = ["h", "s", "sdg", "x", "y", "z", "cx", "cz", "swap"]

    # Random initial state (to get varied expectation values)
    for qubit in range(num_qubits):
        init_choice = np.random.choice(["|0⟩", "|1⟩", "|+⟩", "|-⟩"])
        if init_choice == "|1⟩":
            qc.x(qubit)
        elif init_choice == "|+⟩":
            qc.h(qubit)
        elif init_choice == "|-⟩":
            qc.x(qubit)
            qc.h(qubit)

    for layer in range(depth):
        # Ensure qubit 0 gets operations
        gate = np.random.choice(clifford_gates[:-3])  # Single-qubit gates
        if gate == "h":
            qc.h(0)
        elif gate == "s":
            qc.s(0)
        elif gate == "sdg":
            qc.sdg(0)
        elif gate == "x":
            qc.x(0)
        elif gate == "y":
            qc.y(0)
        elif gate == "z":
            qc.z(0)

        for qubit in range(1, num_qubits):
            # Random Clifford gate on other qubits
            gate = np.random.choice(clifford_gates[:-3])  # Single-qubit gates
            if gate == "h":
                qc.h(qubit)
            elif gate == "s":
                qc.s(qubit)
            elif gate == "sdg":
                qc.sdg(qubit)
            elif gate == "x":
                qc.x(qubit)
            elif gate == "y":
                qc.y(qubit)
            elif gate == "z":
                qc.z(qubit)

        # Random 2-qubit Clifford gates
        for qubit in range(num_qubits - 1):
            if np.random.random() < 0.5:  # 50% chance
                gate = np.random.choice(clifford_gates[-3:])  # 2-qubit gates
                if gate == "cx":
                    qc.cx(qubit, qubit + 1)
                elif gate == "cz":
                    qc.cz(qubit, qubit + 1)
                elif gate == "swap":
                    qc.swap(qubit, qubit + 1)

    return qc


def generate_training_set(num_circuits=50, num_qubits=2, max_depth=5):
    """
    Generate a set of near-Clifford training circuits.

    Args:
        num_circuits (int): Number of training circuits to generate
        num_qubits (int): Number of qubits per circuit
        max_depth (int): Maximum circuit depth

    Returns:
        list[QuantumCircuit]: List of training circuits
    """
    training_circuits = []

    for i in range(num_circuits):
        depth = np.random.randint(1, max_depth + 1)
        circuit = generate_near_clifford_circuit(num_qubits, depth, seed=i)
        training_circuits.append(circuit)

    return training_circuits


def simulate_circuit_expectation(circuit, simulator, shots=2048, observable="Z0"):
    """
    Simulate a circuit and compute expectation value of an observable.

    Args:
        circuit (QuantumCircuit): Circuit to simulate
        simulator: Qiskit AerSimulator (ideal or noisy)
        shots (int): Number of measurement shots
        observable (str): Observable to measure ('Z0', 'Z1', etc.)

    Returns:
        float: Expectation value <observable>
    """
    # Remove existing measurements
    qc = circuit.remove_final_measurements(inplace=False)

    # Add measurement for the observable
    if observable.startswith("Z"):
        qubit_idx = int(observable[1:])
        if qc.num_clbits == 0:
            qc.add_register(ClassicalRegister(qc.num_qubits, "c"))
        qc.measure(qubit_idx, qubit_idx)

        # Run simulation
        result = simulator.run(qc, shots=shots).result()
        counts = result.get_counts()

        # Compute <Z> = P(0) - P(1)
        total_shots = sum(counts.values())
        # Note: Qiskit bit ordering - bits[0] is highest qubit, bits[-1] is lowest
        qubit_bit_idx = -(qubit_idx + 1)  # qubit 0 -> bits[-1], qubit 1 -> bits[-2]
        prob_0 = (
            sum(cnt for bits, cnt in counts.items() if bits[qubit_bit_idx] == "0") / total_shots
        )
        prob_1 = (
            sum(cnt for bits, cnt in counts.items() if bits[qubit_bit_idx] == "1") / total_shots
        )

        expectation = prob_0 - prob_1
        return expectation

    else:
        raise ValueError(f"Observable {observable} not supported")


def collect_training_data(training_circuits, ideal_simulator, noisy_simulator, shots=2048):
    """
    Collect training data: pairs of (noisy_expectation, exact_expectation).

    Args:
        training_circuits (list[QuantumCircuit]): Training circuits
        ideal_simulator: Simulator without noise
        noisy_simulator: Simulator with noise model
        shots (int): Shots per circuit

    Returns:
        tuple: (noisy_expectations, exact_expectations) as numpy arrays
    """
    noisy_expectations = []
    exact_expectations = []

    for circuit in training_circuits:
        # Simulate on noisy hardware
        noisy_exp = simulate_circuit_expectation(circuit, noisy_simulator, shots)

        # Simulate exactly (ideal)
        exact_exp = simulate_circuit_expectation(circuit, ideal_simulator, shots)

        noisy_expectations.append(noisy_exp)
        exact_expectations.append(exact_exp)

    return np.array(noisy_expectations), np.array(exact_expectations)


def fit_cdr_regression(noisy_expectations, exact_expectations):
    """
    Fit linear regression model: exact = a * noisy + b

    Args:
        noisy_expectations (array): Noisy expectation values (features)
        exact_expectations (array): Exact expectation values (targets)

    Returns:
        tuple: (slope, intercept, model_score)
    """
    # Reshape for sklearn (expects 2D array)
    X = noisy_expectations.reshape(-1, 1)  # Features: noisy values
    y = exact_expectations  # Targets: exact values

    # Fit linear regression
    model = LinearRegression()
    model.fit(X, y)

    # Extract parameters
    slope = model.coef_[0]
    intercept = model.intercept_
    score = model.score(X, y)  # R² score

    return slope, intercept, score


def apply_cdr_correction(noisy_value, slope, intercept):
    """
    Apply learned CDR correction to a noisy expectation value.

    Args:
        noisy_value (float): Noisy expectation value
        slope (float): Regression slope
        intercept (float): Regression intercept

    Returns:
        float: Corrected expectation value
    """
    return slope * noisy_value + intercept


# ---------------------------------------------------------------------------
# CDRMitigator class
# ---------------------------------------------------------------------------


class CDRMitigator(Mitigator):
    """Clifford Data Regression via training on near-Clifford circuits."""

    def __init__(self, num_training_circuits=50, num_qubits=2, max_depth=5, num_shots=1024):
        """
        Parameters
        ----------
        num_training_circuits : int, optional
            Number of near-Clifford circuits to generate for training. Default: 50.
        num_qubits : int, optional
            Number of qubits in training circuits. Default: 2.
        max_depth : int, optional
            Maximum depth of training circuits. Default: 5.
        num_shots : int, optional
            Number of shots per training circuit. Default: 1024.
        """
        self.num_training_circuits = num_training_circuits
        self.num_qubits = num_qubits
        self.max_depth = max_depth
        self.num_shots = num_shots

        # Training state (set by fit() method)
        self.slope = None
        self.intercept = None
        self.r2_score = None
        self.training_circuits = None

    def fit(self, noisy_simulator, ideal_simulator=None):
        """
        Train the CDR model on near-Clifford circuits.

        Parameters
        ----------
        noisy_simulator : AerSimulator
            Simulator with noise model for collecting noisy training data.
        ideal_simulator : AerSimulator, optional
            Simulator without noise for collecting exact training data.
            Defaults to noiseless AerSimulator.

        Returns
        -------
        dict with training results:
            "slope" — regression slope
            "intercept" — regression intercept
            "r2_score" — model fit quality (R²)
            "training_circuits" — list of training circuits used
        """
        if ideal_simulator is None:
            ideal_simulator = AerSimulator()

        # Generate training circuits
        self.training_circuits = generate_training_set(
            self.num_training_circuits, self.num_qubits, self.max_depth
        )

        # Collect training data
        noisy_train, exact_train = collect_training_data(
            self.training_circuits, ideal_simulator, noisy_simulator, self.num_shots
        )

        # Fit regression model
        self.slope, self.intercept, self.r2_score = fit_cdr_regression(noisy_train, exact_train)

        return {
            "slope": self.slope,
            "intercept": self.intercept,
            "r2_score": self.r2_score,
            "training_circuits": self.training_circuits,
        }

    def mitigate(self, circuit, observable=None, backend=None):
        """
        Apply CDR correction to estimate the mitigated expectation value.

        Parameters
        ----------
        circuit : QuantumCircuit
            The circuit to mitigate. May contain measurements; they are
            stripped internally.
        observable : ignored
            Reserved for future use. Currently <Z₀> on qubit 0 is always measured.
        backend : AerSimulator or None
            Simulator to run the circuit on. If None, uses the noisy simulator
            from training (if available) or raises an error.

        Returns
        -------
        dict with keys:
            "mitigated" — CDR-corrected expectation value
            "noisy" — raw noisy expectation value
            "slope" — regression slope used
            "intercept" — regression intercept used
        """
        if self.slope is None or self.intercept is None:
            raise ValueError("CDR model not trained. Call fit() first.")

        if backend is None:
            raise ValueError("backend must be provided for mitigation")

        # Measure raw noisy value
        noisy_value = simulate_circuit_expectation(circuit, backend, shots=self.num_shots)

        # Apply CDR correction
        mitigated_value = apply_cdr_correction(noisy_value, self.slope, self.intercept)

        return {
            "mitigated": mitigated_value,
            "noisy": noisy_value,
            "slope": self.slope,
            "intercept": self.intercept,
        }

    def overhead(self):
        """CDR overhead = n_training_circuits + 1 (the target circuit)."""
        return float(self.n_training_circuits + 1)

    def name(self):
        return "CDR (Clifford Data Regression)"
