from __future__ import annotations

from qiskit import QuantumCircuit

from qcharge_core import QChargeInstance, build_qubo


def build_fixed_qaoa_circuit(
    instance: QChargeInstance,
    gammas: list[float],
    betas: list[float],
    *,
    measure: bool = True,
    barriers: bool = False,
) -> QuantumCircuit:
    """Build a fixed-parameter QAOA circuit for E(x)=x.T Q x + offset.

    Mapping:
        x_i = (1 - Z_i) / 2

    Diagonal QUBO term a*x_i:
        exp(-i gamma a x_i) -> RZ(-gamma*a), up to global phase.

    Pair term b*x_i*x_j:
        x_i*x_j = (I - Zi - Zj + ZiZj)/4
        -> RZ(-gamma*b/2) on i and j
        -> RZZ(gamma*b/2) on (i,j), up to global phase.

    Mixer:
        exp(-i beta X) -> RX(2*beta)
    """
    if len(gammas) != len(betas):
        raise ValueError("gammas and betas must have equal length")

    Q, _offset = build_qubo(instance)
    n = instance.n_qubits
    qc = QuantumCircuit(n, n if measure else 0, name=f"QCHARGE_p{len(gammas)}")

    for q in range(n):
        qc.h(q)

    if barriers:
        qc.barrier()

    for gamma, beta in zip(gammas, betas, strict=True):
        for i in range(n):
            a = float(Q[i, i])
            if abs(a) > 1e-15:
                qc.rz(-gamma * a, i)

        for i in range(n):
            for j in range(i + 1, n):
                b = float(Q[i, j])
                if abs(b) <= 1e-15:
                    continue
                qc.rz(-gamma * b / 2.0, i)
                qc.rz(-gamma * b / 2.0, j)
                qc.rzz(gamma * b / 2.0, i, j)

        if barriers:
            qc.barrier()

        for q in range(n):
            qc.rx(2.0 * beta, q)

        if barriers:
            qc.barrier()

    if measure:
        qc.measure(range(n), range(n))

    return qc
