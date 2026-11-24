"""Warmtenet under uncertainty: instances for Assignment 2 of MO 2026-27.

RELEASE NOTE (staff): this module rebuilds the optimal Assignment-1 design of each student's district, so it must not
be pushed to the public repository before the Assignment-1 deadline has passed.

Scenarios are built from the coldest daily mean temperature of each winter (November-March) at De Bilt (KNMI station
260), winters 1951-2026; the winter of 1951 runs from November 1950 to March 1951. Source: Royal Netherlands
Meteorological Institute (KNMI), daily data (field TG); provenance and extraction in data/README.md. The temperatures
are real; the neighborhood demands derived from them are simulated with a stylized peak-demand model.
"""

from importlib import resources

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from .common import personal_seed
from .warmtenet import make_instance

T_REF, T_DESIGN = 18.0, -10.0         # heating threshold and design temperature (°C)
TRAIN, TEST = (1951, 1995), (1996, 2026)
UPGRADE_COST_FACTOR = 0.8             # upgrading (a parallel pipe: double capacity) costs 80% of the original pipe
BACKUP_COST = 70.0                    # k€/yr per MW of peak demand covered by rented mobile boilers
LOCAL_CAPACITY_COST = 14.0            # k€/yr per MW of local peak-boiler capacity installed at a neighborhood
LOCAL_HEAT_COST = 30.0                # k€/yr per MW produced by a local peak boiler on the peak day
NOISE = 0.05                          # neighborhood-specific multiplicative noise (log-normal sigma)
N_GROWTH_AREAS = 4                    # neighborhoods designated for new housing since Assignment 1
GROWTH_RANGE = (1.3, 1.6)             # design-demand growth factor in those neighborhoods
RESERVATION_COST = {"Waste incinerator": 12.0, "Data center": 10.0, "Aquathermal plant": 11.0,
                    "Gas peak boilers": 4.0}


def winters():
    """Coldest daily mean temperature (°C) of every winter 1951-2026 at De Bilt (KNMI)."""
    path = resources.files("mo2026") / "data" / "debilt_coldest_day_per_winter.csv"
    return pd.read_csv(path, index_col="winter")


def _a1_design(base):
    """Cheapest Assignment-1 design that connects as many neighborhoods as possible (all of them, unless pipe or
    source capacities make that impossible), with the aggregated formulation, solved to optimality."""
    m = pyo.ConcreteModel()
    out_arcs = {i: [a for a in base.A if a[0] == i] for i in base.V}
    in_arcs = {i: [a for a in base.A if a[1] == i] for i in base.V}
    m.y = pyo.Var(base.E, domain=pyo.Binary)
    m.o = pyo.Var(base.S, domain=pyo.Binary)
    m.z = pyo.Var(base.K, domain=pyo.Binary)
    m.x = pyo.Var(base.A, domain=pyo.NonNegativeReals)
    m.g = pyo.Var(base.S, domain=pyo.NonNegativeReals)
    big = 10 * (sum(base.open_cost.values()) + sum(base.pipe_cost.values()) + sum(base.hp_cost.values())
                + max(base.heat_cost.values()) * sum(base.demand.values()))  # connecting one more always pays
    m.cost = pyo.Objective(expr=sum(base.open_cost[s] * m.o[s] + base.heat_cost[s] * m.g[s] for s in base.S)
                           + sum(base.pipe_cost[e] * m.y[e] for e in base.E)
                           + sum(base.transport_cost[base.edge(i, j)] * m.x[i, j] for (i, j) in base.A)
                           + sum((base.hp_cost[k] + big) * (1 - m.z[k]) for k in base.K))
    m.balance = pyo.Constraint(base.V, rule=lambda m, i: (
        sum(m.x[a] for a in in_arcs[i]) - sum(m.x[a] for a in out_arcs[i]) + (m.g[i] if i in base.S else 0)
        == (base.demand[i] * m.z[i] if i in base.K else 0)))
    m.link = pyo.Constraint(base.E, rule=lambda m, i, j: m.x[i, j] + m.x[j, i] <= base.pipe_cap[i, j] * m.y[i, j])
    m.src = pyo.Constraint(base.S, rule=lambda m, s: m.g[s] <= base.capacity[s] * m.o[s])
    opt = pyo.SolverFactory("appsi_highs")
    opt.options["mip_rel_gap"] = 0.0
    opt.solve(m)
    built = sorted(e for e in base.E if pyo.value(m.y[e]) > 0.5)
    opened = sorted(s for s in base.S if pyo.value(m.o[s]) > 0.5)
    connected = sorted(k for k in base.K if pyo.value(m.z[k]) > 0.5)
    production = {s: round(pyo.value(m.g[s]), 6) for s in opened}
    return built, opened, connected, production


class InstanceA2:
    """A Warmtenet-under-uncertainty instance. Main attributes:

    - base: the Assignment-1 instance of your district (for plotting)
    - V: nodes of the network; E_old: existing pipes; E_new: candidate new pipes (loops); E = E_old + E_new;
      A: arcs (both directions of every pipe in E); out_arcs[i], in_arcs[i]: arcs leaving / entering node i
    - cap[e] (MW): capacity of an existing pipe, or of a new pipe if built; upgrading an existing pipe adds a parallel
      pipe and doubles its capacity; upgrade_cost[e] (existing pipes) and build_cost[e] (new pipes), k€/yr;
      transport_cost[e]
    - S: sources (opened in Assignment 1); max_capacity[s] (MW); reservation_cost[s] (k€/yr per MW reserved);
      heat_cost[s] (k€/yr per MW produced on the peak day); design_production[s] (MW produced on the design day)
    - K: connected neighborhoods (normally all of them); design_demand[k] (MW at -10 °C, including growth); growth[k] (factor with
      respect to Assignment 1); base_share[k]
    - local_capacity_cost, local_heat_cost: a local peak boiler at a neighborhood (k€/yr per MW installed / produced);
      local_max[k]: maximum local capacity (MW)
    - backup_cost (k€/yr per MW covered by rented mobile boilers)
    - train_temperature, train_demand: coldest daily mean (°C) and neighborhood peak demand (MW) for training winters
    - test_temperature, test_demand: corresponding later winters, supplied for context
    """

    def __repr__(self):
        return (f"Warmtenet-A2 instance: {len(self.V)} nodes, {len(self.E_old)} existing pipes, "
                f"{len(self.E_new)} candidate new pipes, {len(self.S)} sources, {len(self.K)} connected neighborhoods, "
                f"{len(self.train_demand)} training winters")

    @property
    def A(self):
        return [(i, j) for (i, j) in self.E] + [(j, i) for (i, j) in self.E]

    @property
    def out_arcs(self):
        """out_arcs[i]: list of the arcs (i, j) that leave node i."""
        out = {i: [] for i in self.V}
        for (i, j) in self.A:
            out[i].append((i, j))
        return out

    @property
    def in_arcs(self):
        """in_arcs[j]: list of the arcs (i, j) that enter node j."""
        inn = {i: [] for i in self.V}
        for (i, j) in self.A:
            inn[j].append((i, j))
        return inn

    def edge(self, i, j):
        return (i, j) if i < j else (j, i)

    def demand_at(self, temperature, noise=None):
        """Peak demand per neighborhood (dict) at a given coldest-day temperature, without noise by default."""
        f = {k: self.base_share[k] + (1 - self.base_share[k]) * (T_REF - temperature) / (T_REF - T_DESIGN)
             for k in self.K}
        return {k: self.design_demand[k] * f[k] * (1.0 if noise is None else noise[k]) for k in self.K}


def make_instance_a2(student_number):
    """Return your personal Assignment-2 instance (your district and the network built after Assignment 1)."""
    base = make_instance(student_number)
    built, opened, connected, production = _a1_design(base)
    rng = np.random.default_rng(personal_seed(student_number, "A2"))

    inst = InstanceA2()
    inst.base = base
    nodes = sorted({n for e in built for n in e} | set(opened) | set(connected))
    inst.V = nodes
    inst.E_old = list(built)
    inst.E_new = [e for e in base.E if e not in set(built) and e[0] in nodes and e[1] in nodes]
    inst.E = inst.E_old + inst.E_new
    inst.cap = {e: base.pipe_cap[e] for e in inst.E}
    inst.upgrade_cost = {e: round(UPGRADE_COST_FACTOR * base.pipe_cost[e], 1) for e in inst.E_old}
    inst.build_cost = {e: base.pipe_cost[e] for e in inst.E_new}
    inst.transport_cost = {e: base.transport_cost[e] for e in inst.E}
    inst.upgrade_capacity = {e: base.pipe_cap[e] for e in inst.E_old}
    inst.S = list(opened)
    inst.source_name = {s: base.source_name[s] for s in opened}
    inst.max_capacity = {s: base.capacity[s] for s in opened}
    inst.reservation_cost = {s: RESERVATION_COST[base.source_name[s]] for s in opened}
    inst.heat_cost = {s: base.heat_cost[s] for s in opened}
    inst.design_production = production
    inst.K = list(connected)
    growth_areas = set(int(k) for k in rng.choice(inst.K, size=N_GROWTH_AREAS, replace=False))
    inst.growth = {k: round(float(rng.uniform(*GROWTH_RANGE)), 2) if k in growth_areas else 1.0 for k in inst.K}
    inst.design_demand = {k: round(base.demand[k] * inst.growth[k], 2) for k in connected}
    inst.base_share = {k: 0.15 if base.old[k] else 0.3 for k in connected}
    inst.backup_cost = BACKUP_COST
    inst.local_capacity_cost = LOCAL_CAPACITY_COST
    inst.local_heat_cost = LOCAL_HEAT_COST
    inst.local_max = {k: float(inst.design_demand[k]) for k in connected}

    w = winters()["coldest_day_mean_C"]
    inst.train_temperature = w.loc[TRAIN[0]:TRAIN[1]]
    inst.test_temperature = w.loc[TEST[0]:TEST[1]]
    all_noise = np.exp(rng.normal(0.0, NOISE, size=(len(w), len(inst.K))) - NOISE ** 2 / 2)
    noise = pd.DataFrame(all_noise, index=w.index, columns=inst.K)
    demand = pd.DataFrame({yr: inst.demand_at(t, noise.loc[yr]) for yr, t in w.items()}).T.round(3)
    demand.index.name = "winter"
    inst.train_demand = demand.loc[TRAIN[0]:TRAIN[1]]
    inst.test_demand = demand.loc[TEST[0]:TEST[1]]
    return inst


def one_source_example(student_number):
    """Your one-source reservation example: total training demand per winter, and the costs."""
    inst = make_instance_a2(student_number)
    total = inst.train_demand.sum(axis=1).round(3)
    rng = np.random.default_rng(personal_seed(student_number, "A2-onesource"))
    return {"demand": total.to_dict(), "reservation_cost": round(float(rng.uniform(6, 14)), 1),
            "heat_cost": round(float(rng.uniform(6, 10)), 1), "backup_cost": BACKUP_COST}


def plot_network_a2(inst, upgraded=(), new_pipes=(), reservation=None, ax=None, title=None):
    """Draw the existing network (red), upgraded pipes (thick), new pipes (purple), candidate pipes (dotted)."""
    import matplotlib.pyplot as plt
    from .warmtenet import plot_instance

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 6))
    plot_instance(inst.base, ax=ax, title=title or "Assignment 2: the existing network (design demands incl. growth)",
                  demand=inst.design_demand)
    c = inst.base.coords
    for e in inst.E_new:
        ax.plot([c[e[0]][0], c[e[1]][0]], [c[e[0]][1], c[e[1]][1]], ls=":", color="#7d3c98", lw=1.5, zorder=2.4)
    for e in inst.E_old:
        lw = 6.0 if inst.edge(*e) in {inst.edge(*u) for u in upgraded} else 3.0
        ax.plot([c[e[0]][0], c[e[1]][0]], [c[e[0]][1], c[e[1]][1]], color="#c0392b", lw=lw, alpha=0.85, zorder=2.5)
    for e in new_pipes:
        e = inst.edge(*e)
        ax.plot([c[e[0]][0], c[e[1]][0]], [c[e[0]][1], c[e[1]][1]], color="#7d3c98", lw=3.5, zorder=2.6)
    if reservation is not None:
        for s, r in reservation.items():
            ax.annotate(f"reserved {r:.1f} MW", c[s], textcoords="offset points", xytext=(7, 6), fontsize=7,
                        color="#c0392b")
    for k in inst.base.K:
        if k not in inst.K:
            ax.scatter(*c[k], s=25 * inst.base.demand[k], c="white", edgecolors="0.6", zorder=3.5)
    return ax
