# Q-CHARGE PoC v2 — 9-Qubit Benchmark Report

## 1. Objective

This proof-of-concept tests whether a small peer-to-peer EV charging assignment problem can be encoded as a QUBO and processed using QAOA before requesting real EuroHPC quantum-hardware access.

The experiment is intentionally small enough for exact classical verification.

## 2. Experimental Instance

Three EV drivers are matched to three private charging slots. Each binary variable `x[d,s]` indicates whether driver `d` is assigned to charging slot `s`, giving **9 binary variables / qubits**.

| Driver | S1 | S2 | S3 |
|---|---:|---:|---:|
| D1 | 1.25 | 1.10 | 2.40 |
| D2 | 1.05 | 2.00 | 1.35 |
| D3 | 1.70 | 1.20 | 1.10 |

Lower values represent better marketplace matches.

Constraints:
- exactly one charging slot per driver;
- at most one driver per charging slot.

The QUBO penalty coefficient was set to **λ = 2.50**. For this instance, the calculated critical coefficient above which the exact feasible solution remains the QUBO ground state is **λ > 1.10**.

## 3. Exact Classical Baseline

The full binary search space contains **512 states**. Only **6 states** satisfy all assignment constraints.

**Exact optimum:** D1→S2, D2→S1, D3→S3  
**Objective cost:** 3.2500

## 4. QAOA Statevector Benchmark

| Method | Penalised expectation | Feasible probability | Optimal-solution probability | Best feasible cost |
|---|---:|---:|---:|---:|
| QAOA p=1 | 7.0545 | 6.66% | 1.30% | 3.2500 |
| QAOA p=2 | 6.5028 | 3.92% | 1.98% | 3.2500 |
| QAOA p=3 | 5.9195 | 14.83% | **8.48%** | **3.2500** |

At p=3, the exact classical optimum is the highest-probability feasible solution recovered by the QAOA distribution.

Under an illustrative 2,048-shot ideal statevector sampling budget, these probabilities correspond to approximately **304 feasible samples** and **174 optimal samples**. These figures are expectations from the ideal statevector distribution, not real-hardware measurements.

## 5. Interpretation

The PoC demonstrates that:

1. the P2P charging assignment problem can be represented as a compact QUBO;
2. the QUBO ground state can be independently verified with exact classical enumeration;
3. shallow QAOA can place measurable probability mass on the exact optimum;
4. increasing depth from p=1 to p=3 materially improved optimal-solution sampling for this formulation.

The experiment does **not** demonstrate quantum advantage. Its purpose is to validate the formulation and software workflow before repeating the experiment on real quantum hardware, where noise, sampling stability, circuit execution and scaling behaviour become the research questions.

## 6. Penalty sensitivity

An initial penalty coefficient of λ=8 preserved feasibility but produced a difficult low-depth QAOA energy landscape. Penalty sensitivity analysis showed that λ=2.5 still preserves the exact feasible ground state while producing a more useful benchmark distribution.

This motivates treating penalty calibration as an experimental parameter in the proposed hardware work.

## 7. Next EuroHPC Experiment

The real-QPU phase is intended to:

1. reproduce the 9-variable benchmark on hardware;
2. compare ideal-statevector and QPU sampling distributions;
3. record feasibility rate, optimum/near-optimum sampling rate and run-to-run variance;
4. test p=1, p=2 and p=3 subject to hardware constraints;
5. extend to 16- and 20-variable marketplace instances;
6. evaluate penalty calibration and hardware-aware circuit choices.

No claim in this report is based on real quantum hardware. All QAOA results reported here are ideal statevector simulation results.
