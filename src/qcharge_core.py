from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np


@dataclass(frozen=True)
class QChargeInstance:
    name: str
    drivers: list[str]
    slots: list[str]
    cost_matrix: np.ndarray
    penalty_lambda: float

    @property
    def n_drivers(self) -> int:
        return len(self.drivers)

    @property
    def n_slots(self) -> int:
        return len(self.slots)

    @property
    def n_qubits(self) -> int:
        return self.n_drivers * self.n_slots

    def q(self, driver_index: int, slot_index: int) -> int:
        return driver_index * self.n_slots + slot_index


def load_instance(path: str | Path) -> QChargeInstance:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return QChargeInstance(
        name=data["name"],
        drivers=list(data["drivers"]),
        slots=list(data["slots"]),
        cost_matrix=np.asarray(data["cost_matrix"], dtype=float),
        penalty_lambda=float(data["penalty_lambda"]),
    )


def load_angles(path: str | Path) -> dict[int, dict[str, list[float]]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.items()}


def build_qubo(instance: QChargeInstance) -> tuple[np.ndarray, float]:
    """Build an upper-triangular QUBO matrix Q and constant offset.

    E(x) = x.T @ Q @ x + offset

    Constraints:
      1) exactly one slot per driver;
      2) at most one driver per slot.
    """
    n = instance.n_qubits
    lam = instance.penalty_lambda
    Q = np.zeros((n, n), dtype=float)
    offset = instance.n_drivers * lam

    for d in range(instance.n_drivers):
        for s in range(instance.n_slots):
            i = instance.q(d, s)
            Q[i, i] += instance.cost_matrix[d, s] - lam

        for s1 in range(instance.n_slots):
            for s2 in range(s1 + 1, instance.n_slots):
                i = instance.q(d, s1)
                j = instance.q(d, s2)
                Q[i, j] += 2.0 * lam

    for s in range(instance.n_slots):
        for d1 in range(instance.n_drivers):
            for d2 in range(d1 + 1, instance.n_drivers):
                i = instance.q(d1, s)
                j = instance.q(d2, s)
                Q[min(i, j), max(i, j)] += lam

    return Q, float(offset)


def direct_penalized_energy(bits_q0_first, instance: QChargeInstance) -> float:
    bits = np.asarray(bits_q0_first, dtype=int)
    x = bits.reshape(instance.n_drivers, instance.n_slots)
    raw = float(np.sum(x * instance.cost_matrix))
    penalty_units = 0.0

    for d in range(instance.n_drivers):
        penalty_units += float((x[d].sum() - 1) ** 2)

    for s in range(instance.n_slots):
        k = int(x[:, s].sum())
        penalty_units += k * (k - 1) / 2

    return raw + instance.penalty_lambda * penalty_units


def qubo_energy(bits_q0_first, Q: np.ndarray, offset: float) -> float:
    x = np.asarray(bits_q0_first, dtype=float)
    return float(x @ Q @ x + offset)


def raw_cost(bits_q0_first, instance: QChargeInstance) -> float:
    bits = np.asarray(bits_q0_first, dtype=int)
    x = bits.reshape(instance.n_drivers, instance.n_slots)
    return float(np.sum(x * instance.cost_matrix))


def is_feasible(bits_q0_first, instance: QChargeInstance) -> bool:
    bits = np.asarray(bits_q0_first, dtype=int)
    x = bits.reshape(instance.n_drivers, instance.n_slots)
    return bool(np.all(x.sum(axis=1) == 1) and np.all(x.sum(axis=0) <= 1))


def assignment_label(bits_q0_first, instance: QChargeInstance) -> str:
    bits = np.asarray(bits_q0_first, dtype=int)
    x = bits.reshape(instance.n_drivers, instance.n_slots)
    out = []
    for d, driver in enumerate(instance.drivers):
        slots = np.where(x[d] == 1)[0]
        if len(slots) == 1:
            out.append(f"{driver}→{instance.slots[int(slots[0])]}")
        else:
            out.append(f"{driver}→invalid")
    return ", ".join(out)


def exact_solution(instance: QChargeInstance) -> dict:
    n = instance.n_qubits
    best = None
    feasible_count = 0

    for z in range(2**n):
        bits = np.array([(z >> q) & 1 for q in range(n)], dtype=int)
        if not is_feasible(bits, instance):
            continue
        feasible_count += 1
        cost = raw_cost(bits, instance)
        if best is None or cost < best["raw_cost"]:
            best = {
                "bits_q0_first": bits.tolist(),
                "qiskit_bitstring": "".join(str(v) for v in bits[::-1]),
                "raw_cost": cost,
                "assignment": assignment_label(bits, instance),
            }

    assert best is not None
    best["feasible_count"] = feasible_count
    best["search_space"] = 2**n
    return best


def normalize_qiskit_bitstring(bitstring: str, n_qubits: int) -> str:
    clean = bitstring.replace(" ", "").replace("_", "")
    if len(clean) != n_qubits:
        raise ValueError(f"Expected {n_qubits} measured bits, got {len(clean)} from {bitstring!r}")
    if any(c not in "01" for c in clean):
        raise ValueError(f"Invalid bitstring: {bitstring!r}")
    return clean


def qiskit_bitstring_to_q0_bits(bitstring: str, n_qubits: int) -> np.ndarray:
    """Convert Qiskit's displayed c[n-1]...c[0] string to q0...q[n-1]."""
    clean = normalize_qiskit_bitstring(bitstring, n_qubits)
    return np.array([int(c) for c in clean[::-1]], dtype=int)


def analyze_counts(counts: dict[str, int], instance: QChargeInstance) -> dict:
    Q, offset = build_qubo(instance)
    exact = exact_solution(instance)
    total = int(sum(int(v) for v in counts.values()))
    if total <= 0:
        raise ValueError("Counts are empty.")

    feasible_shots = 0
    optimal_shots = 0
    weighted_qubo = 0.0
    weighted_raw_feasible = 0.0
    best_feasible = None
    rows = []

    for bitstring, count in counts.items():
        count = int(count)
        bits = qiskit_bitstring_to_q0_bits(bitstring, instance.n_qubits)
        feas = is_feasible(bits, instance)
        raw = raw_cost(bits, instance)
        qe = qubo_energy(bits, Q, offset)
        label = assignment_label(bits, instance)
        is_opt = feas and abs(raw - exact["raw_cost"]) < 1e-12 and label == exact["assignment"]

        weighted_qubo += count * qe
        if feas:
            feasible_shots += count
            weighted_raw_feasible += count * raw
            if best_feasible is None or raw < best_feasible["raw_cost"]:
                best_feasible = {
                    "raw_cost": raw,
                    "assignment": label,
                    "qiskit_bitstring": normalize_qiskit_bitstring(bitstring, instance.n_qubits),
                }
        if is_opt:
            optimal_shots += count

        rows.append({
            "qiskit_bitstring": normalize_qiskit_bitstring(bitstring, instance.n_qubits),
            "count": count,
            "probability": count / total,
            "feasible": feas,
            "optimal": is_opt,
            "raw_cost": raw,
            "qubo_energy": qe,
            "assignment": label,
        })

    rows.sort(key=lambda r: (-r["count"], r["qubo_energy"]))

    return {
        "shots": total,
        "feasible_shots": feasible_shots,
        "feasible_probability": feasible_shots / total,
        "optimal_shots": optimal_shots,
        "optimal_solution_probability": optimal_shots / total,
        "mean_qubo_energy": weighted_qubo / total,
        "conditional_mean_raw_cost": weighted_raw_feasible / feasible_shots if feasible_shots else None,
        "best_feasible": best_feasible,
        "exact": exact,
        "states": rows,
    }
