#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
sys.path.insert(0, str(SRC))

import pandas as pd

from qcharge_core import load_instance, load_angles, analyze_counts, exact_solution
from qcharge_circuit import build_fixed_qaoa_circuit


def parse_args():
    p = argparse.ArgumentParser(
        description="Q-CHARGE fixed-parameter QAOA benchmark for Piast-Q/AQT."
    )
    p.add_argument(
        "--backend",
        choices=["local", "piast-q"],
        default="local",
        help="local = Qiskit/QLauncher simulator; piast-q = AQT real-device access.",
    )
    p.add_argument(
        "--depths",
        nargs="+",
        type=int,
        default=[1, 2, 3],
        choices=[1, 2, 3],
    )
    p.add_argument("--shots", type=int, default=2048)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--transpile-level", type=int, choices=[0, 1, 2, 3], default=2)
    p.add_argument("--dotenv", default=".env")
    p.add_argument(
        "--confirm-hardware",
        action="store_true",
        help="Required safety switch before any real-QPU submission.",
    )
    p.add_argument(
        "--expected-backend-substring",
        default="",
        help="Optional backend-name safety check.",
    )
    p.add_argument("--instance", default=str(HERE / "config" / "instance_3x3.json"))
    p.add_argument("--angles", default=str(HERE / "config" / "optimized_angles.json"))
    p.add_argument("--output-dir", default=str(HERE / "results"))
    return p.parse_args()


def build_backend(args):
    if args.backend == "local":
        from qlauncher.routines.qiskit import QiskitBackend
        return QiskitBackend("local_simulator")

    if not args.confirm_hardware:
        raise SystemExit(
            "REFUSED: real Piast-Q mode requires --confirm-hardware. "
            "Run local validation first."
        )

    dotenv = Path(args.dotenv).resolve()
    if not dotenv.exists():
        raise SystemExit(
            f"REFUSED: token file not found: {dotenv}. "
            "Create a local .env file containing the allocation token."
        )

    from qlauncher.routines.qiskit.backends.aqt_backend import AQTBackend
    backend = AQTBackend(
        name="device",
        dotenv_path=str(dotenv),
        auto_transpile_level=args.transpile_level,
    )

    if args.expected_backend_substring:
        expected = args.expected_backend_substring.lower()
        resolved = str(getattr(backend, "name", "")).lower()
        if expected not in resolved:
            raise SystemExit(
                f"REFUSED: resolved backend {backend.name!r} does not contain "
                f"expected substring {args.expected_backend_substring!r}."
            )

    return backend


def main():
    args = parse_args()
    instance = load_instance(args.instance)
    angles = load_angles(args.angles)
    exact = exact_solution(instance)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.output_dir) / f"{args.backend}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)

    backend = build_backend(args)
    backend_name = str(getattr(backend, "name", type(backend).__name__))

    metadata = {
        "timestamp_utc": timestamp,
        "backend_mode": args.backend,
        "resolved_backend_name": backend_name,
        "shots_requested_per_circuit": args.shots,
        "repeats": args.repeats,
        "depths": args.depths,
        "transpile_level": args.transpile_level if args.backend == "piast-q" else None,
        "instance": instance.name,
        "n_qubits": instance.n_qubits,
        "exact_solution": exact,
        "notes": (
            "Real-device mode uses QLauncher's AQTBackend(name='device'). "
            "The allocation token determines which authorised online AQT device is available."
        ),
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary_rows = []

    for depth in args.depths:
        gamma = angles[depth]["gammas"]
        beta = angles[depth]["betas"]
        circuit = build_fixed_qaoa_circuit(instance, gamma, beta, measure=True)

        (run_dir / f"circuit_p{depth}.txt").write_text(
            str(circuit.draw(output="text")), encoding="utf-8"
        )

        for repeat in range(1, args.repeats + 1):
            print(
                f"[RUN] backend={backend_name} p={depth} "
                f"repeat={repeat}/{args.repeats} shots={args.shots}",
                flush=True,
            )

            counts = backend.sample_circuit(circuit, shots=args.shots)
            counts = {str(k): int(v) for k, v in counts.items()}
            (run_dir / f"counts_p{depth}_r{repeat}.json").write_text(
                json.dumps(counts, indent=2, sort_keys=True), encoding="utf-8"
            )

            analysis = analyze_counts(counts, instance)
            states = pd.DataFrame(analysis.pop("states"))
            states.to_csv(run_dir / f"states_p{depth}_r{repeat}.csv", index=False)

            best = analysis.get("best_feasible") or {}
            summary_rows.append({
                "backend": backend_name,
                "depth_p": depth,
                "repeat": repeat,
                "shots": analysis["shots"],
                "feasible_probability": analysis["feasible_probability"],
                "optimal_solution_probability": analysis["optimal_solution_probability"],
                "mean_qubo_energy": analysis["mean_qubo_energy"],
                "conditional_mean_raw_cost": analysis["conditional_mean_raw_cost"],
                "best_feasible_cost": best.get("raw_cost"),
                "best_feasible_assignment": best.get("assignment"),
                "exact_cost": analysis["exact"]["raw_cost"],
                "exact_assignment": analysis["exact"]["assignment"],
            })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(run_dir / "benchmark_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"\nResults: {run_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
