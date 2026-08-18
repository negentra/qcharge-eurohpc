# Q-CHARGE — EuroHPC Quantum Access Pilot

**Quantum-Assisted Optimisation for Peer-to-Peer EV Charging Networks**

Q-CHARGE is a research prototype developed by **Negentra Yazılım ve Oyun Teknolojileri A.Ş.** to investigate whether constrained matching in peer-to-peer EV charging networks can be formulated as a QUBO and benchmarked with QAOA on real quantum hardware.

This repository accompanies the EuroHPC Quantum Access Pilot application **EHPC-QCP-2026Q02-035**.

## Scope

The current validated reference instance contains **3 EV drivers × 3 private charging slots**, represented by **9 binary variables / qubits**. The implementation includes:

- QUBO construction for constrained driver-to-slot assignment;
- exact classical verification over all **512 binary states**;
- ideal statevector QAOA benchmarks for `p = 1, 2, 3`;
- fixed-parameter QAOA circuit generation;
- Qiskit-compatible RZ/RZZ cost-unitary implementation;
- result decoding and benchmark metrics;
- a Piast-Q-oriented execution workflow using the PCSS QLauncher/AQT backend path.

## Validated reference result

| Metric | Result |
|---|---:|
| Binary variables / qubits | 9 |
| Search space | 512 states |
| Feasible assignments | 6 |
| Exact optimum | `D1 → S2, D2 → S1, D3 → S3` |
| Exact objective | 3.2500 |
| QAOA `p=3` feasible probability | 14.83% |
| QAOA `p=3` exact-optimum probability | 8.48% |

The QUBO representation was independently checked against the direct constrained objective across all 512 states. The maximum numerical discrepancy observed in the validation package was approximately `7.1e-15`.

## Important limitation

**No real Piast-Q execution is claimed in this repository.**

The current evidence establishes formulation correctness, exact classical verification, ideal statevector behaviour and hardware-oriented deployment readiness. The requested EuroHPC access is intended to measure effects that cannot be established with ideal simulation, including hardware noise, sampling stability, feasible-solution recovery, run-to-run variance, transpiled circuit characteristics and scaling behaviour.

This work does **not** claim quantum advantage or quantum speed-up at the current problem scale.

## Repository structure

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── config/
│   ├── instance_3x3.json
│   └── optimized_angles.json
├── src/
│   ├── qcharge_core.py
│   └── qcharge_circuit.py
├── poc/
│   └── qcharge_poc_v2.py
├── hardware/
│   └── run_fixed_benchmark.py
└── results/
    ├── benchmark_summary.csv
    ├── classical_feasible_solutions.csv
    └── cost_matrix.csv
```

## Experimental strategy

The proposed hardware programme is deliberately staged:

1. reproduce the validated 9-qubit benchmark on real hardware;
2. compare ideal and QPU sampling distributions;
3. test shallow QAOA depths `p=1–3`;
4. evaluate penalty sensitivity and run-to-run variance;
5. extend the formulation to 16- and 20-variable instances where technically appropriate.

Variational parameters are initially optimised classically and then fixed before QPU execution to avoid unnecessary consumption of quantum resources during the first hardware-validation stage.

## Software environment

The reference implementation is Python-based and uses NumPy, SciPy, pandas, Qiskit-compatible circuits and PCSS QLauncher for the Piast-Q/AQT execution path.

Install the declared dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Data and confidentiality

Only a **sanitised synthetic benchmark instance** is published here. This repository does not contain production VeeShare source code, user data, credentials, pricing logic, deployment secrets or commercially sensitive marketplace data.

## Contact

**Gürcan Serbest**  
Principal Investigator / Lead Developer  
Negentra Yazılım ve Oyun Teknolojileri A.Ş.  
`gurcan@negentra.com.tr`

## Rights

The code is published for transparency and technical evaluation of the Q-CHARGE research prototype. See `LICENSE` for permitted use.
