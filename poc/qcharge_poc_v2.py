"""
Q-CHARGE PoC v2
3 EV drivers x 3 charging slots = 9 binary variables / qubits.

Exact classical baseline vs statevector QAOA p=1,2,3.
Dependencies: numpy, scipy, pandas
"""
import numpy as np
from scipy.optimize import differential_evolution


drivers = ["D1", "D2", "D3"]
slots = ["S1", "S2", "S3"]
cost = np.array([
    [1.25, 1.10, 2.40],
    [1.05, 2.00, 1.35],
    [1.70, 1.20, 1.10],
], dtype=float)
lam = 2.5
n = 9
dim = 2**n
states = np.array([[(z >> q) & 1 for q in range(n)] for z in range(dim)], dtype=np.int8)
X = states.reshape(dim, 3, 3)
raw = (X * cost).sum((1, 2))
rows = X.sum(2)
cols = X.sum(1)
feasible = (rows == 1).all(1) & (cols <= 1).all(1)
pen = ((rows - 1) ** 2).sum(1).astype(float) + (cols * (cols - 1) / 2).sum(1)
energy = raw + lam * pen
fidx = np.where(feasible)[0]
opt_idx = fidx[np.argmin(raw[fidx])]


def assignment(state):
    x = state.reshape(3, 3)
    out = []
    for d in range(3):
        a = np.where(x[d] == 1)[0]
        out.append(f"D{d+1}->S{a[0]+1}" if len(a) == 1 else f"D{d+1}->invalid")
    return ", ".join(out)


def mixer(psi, beta):
    c = np.cos(beta)
    s = -1j * np.sin(beta)
    out = psi.copy()
    for q in range(n):
        step = 1 << q
        arr = out.reshape(-1, 2, step)
        a = arr[:, 0, :].copy()
        b = arr[:, 1, :].copy()
        arr[:, 0, :] = c * a + s * b
        arr[:, 1, :] = s * a + c * b
        out = arr.reshape(-1)
    return out


def state(params, p):
    psi = np.ones(dim, dtype=np.complex128) / np.sqrt(dim)
    for k in range(p):
        psi *= np.exp(-1j * params[k] * energy)
        psi = mixer(psi, params[p + k])
    return psi


def expectation(params, p):
    pr = np.abs(state(params, p)) ** 2
    return float(pr @ energy)


def run(p, seeds=(11, 42, 84)):
    runs = []
    for seed in seeds:
        bounds = [(0, 2 * np.pi)] * p + [(0, np.pi)] * p
        res = differential_evolution(
            lambda v: expectation(v, p),
            bounds,
            seed=seed,
            popsize=10,
            maxiter=120 if p <= 2 else 180,
            tol=1e-9,
            polish=True,
        )
        pr = np.abs(state(res.x, p)) ** 2
        runs.append((res, pr))

    res, pr = min(runs, key=lambda rp: rp[0].fun)
    bf = fidx[np.argmax(pr[fidx])]
    return {
        "p": p,
        "expectation": float(res.fun),
        "feasible_probability": float(pr[feasible].sum()),
        "optimal_solution_probability": float(pr[opt_idx]),
        "best_feasible_cost": float(raw[bf]),
        "best_feasible_assignment": assignment(states[bf]),
        "params": res.x.tolist(),
    }


print("Exact optimum:", float(raw[opt_idx]), assignment(states[opt_idx]))
for p in (1, 2, 3):
    print(run(p))
