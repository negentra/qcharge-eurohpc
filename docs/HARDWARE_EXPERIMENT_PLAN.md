# Q-CHARGE Piast-Q Hardware Experiment Matrix

## Phase 0 — No QPU

- Run the local reference benchmark.
- Export/inspect fixed circuits before hardware use.
- Confirm exact optimum, bit ordering and result decoding.
- Do not proceed if the local baseline differs from the validated PoC.

## Phase 1 — 9-qubit hardware baseline

Use fixed parameters first rather than on-QPU variational training.

Recommended initial configuration:

- `p = 1, 2, 3`
- `2,048` shots per circuit
- `3` repeats
- penalty `λ = 2.5`

Primary metrics:

- feasible-solution probability;
- exact-optimum probability;
- best feasible objective;
- conditional feasible objective;
- mean QUBO energy;
- run-to-run variance.

Each hardware distribution should be compared with the stored ideal statevector benchmark.

## Phase 2 — Penalty sensitivity

Only after the baseline is stable:

- test selected penalty values around the validated λ=2.5 reference;
- retrain angles locally for each penalty value;
- focus on shallow QAOA depths compatible with hardware behaviour.

## Phase 3 — Optional native variational QAOA

Native on-QPU parameter optimisation should be attempted only after the QPU accounting model and baseline execution are understood. Variational optimisation can consume many circuit evaluations and is therefore not the first hardware step.

## Phase 4 — Scaling

After the 9-qubit pipeline is stable:

- extend to 16 variables / qubits;
- then test a 20-variable / qubit instance where the encoding remains technically meaningful.

Classical exact verification should be retained wherever computationally practical; otherwise mathematical optimisation or heuristic classical references should be used.

## Stop conditions

Stop and inspect before further QPU use if:

- measured bitstrings cannot be decoded consistently;
- no feasible solution is sampled in a complete baseline run;
- the resolved backend is not the allocation-authorised device;
- circuit transpilation fails or expands unexpectedly;
- repeated baseline runs are highly inconsistent.
