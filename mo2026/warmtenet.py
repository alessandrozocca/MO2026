"""Warmtenet: instances and plots for the district-heating assignments of MO 2026-27.

The district (Tweegrachten) and the heat company (Grachtenwarmte) are fictional. The district is stylized: a jittered
street grid with two canals (crossable only at bridges), one main avenue in each direction, four candidate heat
sources and a set of neighborhoods. All costs are annualized and expressed in k€ per year; heat is expressed in MW of
peak demand. Network, costs and demands are synthetic and illustrative, not data of a real city.
"""

import numpy as np
import pandas as pd

from .common import personal_seed

SIZES = {  # rows, columns, number of neighborhoods
    "small": (4, 5, 8),
    "main": (5, 6, 12),
    "large": (6, 6, 14),
}
SPACING = 0.4  # km between neighboring junctions

SOURCE_ROLES = [
    # name, temperature type, opening cost (k€/yr), heat cost (k€/yr per MW), capacity as fraction of total demand
    ("Waste incinerator", "HT", (230, 270), (10, 12), 0.45),
    ("Data center", "LT", (100, 130), (6, 8), 0.25),
    ("Aquathermal plant", "LT", (70, 90), (8, 10), 0.20),
    ("Gas peak boilers", "HT", (30, 45), (35, 40), 0.40),
]
STREET_TYPES = {  # pipe capacity (MW), pipe cost (k€/yr per km)
    "main": (60, 190.0),
    "side": (30, 140.0),
}
TRANSPORT_COST = 1.5  # k€/yr per MW per km (pumping and heat losses)
HP_BASE, HP_OLD = 25.0, 8.0  # heat-pump alternative: k€/yr per MW of peak demand (+ extra for older homes)
LT_PIPE_DISCOUNT = 0.15  # pipes of a low-temperature network are 15% cheaper


class Instance:
    """A Warmtenet instance. Main attributes (all plain Python containers):

    - V: list of nodes (junctions); coords[i] = (x, y) in km
    - E: list of candidate pipes (i, j) with i < j, one per street segment; length[e] in km;
      A: all arcs (both directions); out_arcs[i], in_arcs[i]: arcs leaving / entering node i
    - pipe_cost[e] (k€/yr if built), pipe_cap[e] (MW), street[e] ('main' or 'side'),
      transport_cost[e] (k€/yr per MW of flow, in either direction)
    - S: list of candidate source nodes; source_name[s], source_type[s] ('HT' or 'LT'),
      open_cost[s] (k€/yr), capacity[s] (MW), heat_cost[s] (k€/yr per MW produced)
    - K: list of neighborhood nodes; demand[k] (MW, integer), hp_cost[k] (k€/yr if NOT connected: heat pumps),
      homes[k], social_homes[k], old[k] (True if most homes have energy label worse than B)
    - canals: list of canal segments (for plotting only)
    Data frames for display: `neighborhoods`, `sources`, `pipes`.
    """

    def __repr__(self):
        return (f"Warmtenet instance '{self.name}': {len(self.V)} junctions, {len(self.E)} candidate pipes, "
                f"{len(self.S)} candidate sources, {len(self.K)} neighborhoods, "
                f"total peak demand {sum(self.demand.values())} MW")

    @property
    def A(self):
        """All arcs: both directions of every candidate pipe."""
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
        """The candidate pipe (as stored in E) that contains arc (i, j)."""
        return (i, j) if i < j else (j, i)

    @property
    def neighborhoods(self):
        return pd.DataFrame({
            "demand_MW": self.demand, "hp_cost": self.hp_cost, "homes": self.homes,
            "social_homes": self.social_homes, "old": self.old,
        }).rename_axis("node")

    @property
    def sources(self):
        return pd.DataFrame({
            "name": self.source_name, "type": self.source_type, "open_cost": self.open_cost,
            "capacity_MW": self.capacity, "heat_cost": self.heat_cost,
        }).rename_axis("node")

    @property
    def pipes(self):
        return pd.DataFrame({
            "street": self.street, "length_km": self.length, "pipe_cost": self.pipe_cost,
            "capacity_MW": self.pipe_cap, "transport_cost": self.transport_cost,
        }).rename_axis(["i", "j"])


def _grid(rows, cols, rng):
    nodes = list(range(rows * cols))
    pos = {n: divmod(n, cols) for n in nodes}  # (row, col)
    coords = {n: (SPACING * c + rng.uniform(-0.07, 0.07), SPACING * (rows - 1 - r) + rng.uniform(-0.07, 0.07))
              for n, (r, c) in pos.items()}
    return nodes, pos, coords


def _connected(nodes, edges):
    adj = {n: [] for n in nodes}
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)
    seen, stack = {nodes[0]}, [nodes[0]]
    while stack:
        for j in adj[stack.pop()]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    return len(seen) == len(nodes)


def make_instance(student_number=None, size="main", seed=None):
    """Return your personal Warmtenet instance. Use `size` = 'small', 'main' (default) or 'large'."""
    if seed is None:
        seed = personal_seed(student_number, f"A1-{size}")
    rng = np.random.default_rng(seed)
    rows, cols, n_nb = SIZES[size]
    while True:
        nodes, pos, coords = _grid(rows, cols, rng)
        r_canal = int(rng.integers(1, rows - 2))  # horizontal canal between rows r_canal and r_canal + 1
        c_canal = int(rng.integers(1, cols - 2))  # vertical canal between cols c_canal and c_canal + 1
        r_main = int(rng.choice([r for r in range(rows) if r not in (0, rows - 1)]))
        c_main = int(rng.choice([c for c in range(cols) if c not in (0, cols - 1)]))
        # bridges: where the main avenues cross the canals, plus one extra bridge on each side of the other canal
        h_bridges = {c_main, int(rng.integers(0, c_canal + 1)), int(rng.integers(c_canal + 1, cols))}
        v_bridges = {r_main, int(rng.integers(0, r_canal + 1)), int(rng.integers(r_canal + 1, rows))}
        edges, street = [], {}
        for n in nodes:
            r, c = pos[n]
            if c + 1 < cols and not (c == c_canal and r not in v_bridges):
                e = (n, n + 1)
                edges.append(e)
                street[e] = "main" if r == r_main else "side"
            if r + 1 < rows and not (r == r_canal and c not in h_bridges):
                e = (n, n + cols)
                edges.append(e)
                street[e] = "main" if c == c_main else "side"
        if _connected(nodes, edges):
            break

    inst = Instance()
    inst.name, inst.seed, inst.size = f"{size}-{seed}", seed, size
    inst.V, inst.coords, inst.E, inst.street = nodes, coords, edges, street
    inst.length = {e: round(float(np.hypot(*np.subtract(coords[e[0]], coords[e[1]]))), 3) for e in edges}
    inst.pipe_cap = {e: STREET_TYPES[street[e]][0] for e in edges}
    inst.pipe_cost = {e: round(STREET_TYPES[street[e]][1] * inst.length[e] * rng.uniform(0.9, 1.1), 1) for e in edges}
    inst.transport_cost = {e: round(TRANSPORT_COST * inst.length[e], 3) for e in edges}
    inst.canals = [
        [(coords[r_canal * cols][0] - 0.2, SPACING * (rows - 1 - r_canal - 0.5)),
         (coords[r_canal * cols + cols - 1][0] + 0.2, SPACING * (rows - 1 - r_canal - 0.5))],
        [(SPACING * (c_canal + 0.5), SPACING * (rows - 1) + 0.2), (SPACING * (c_canal + 0.5), -0.2)],
    ]

    # sources: incinerator, data center and gas boilers on the boundary, aquathermal plant next to a canal
    boundary = [n for n in nodes if pos[n][0] in (0, rows - 1) or pos[n][1] in (0, cols - 1)]
    canal_side = [n for n in nodes if pos[n][0] in (r_canal, r_canal + 1) or pos[n][1] in (c_canal, c_canal + 1)]
    chosen = []
    for role in range(4):
        base = canal_side if role == 2 else boundary
        for min_dist in (3, 2, 1):  # keep sources apart; relax only if no node qualifies
            pool = [n for n in base if n not in chosen and all(
                abs(pos[n][0] - pos[m][0]) + abs(pos[n][1] - pos[m][1]) >= min_dist for m in chosen)]
            if pool:
                break
        chosen.append(int(rng.choice(pool)))
    inst.S = chosen
    rest = [n for n in nodes if n not in chosen]
    inst.K = sorted(int(n) for n in rng.choice(rest, size=n_nb, replace=False))

    inst.demand = {k: int(rng.integers(4, 15)) for k in inst.K}
    inst.old = {k: bool(rng.random() < 0.5) for k in inst.K}
    inst.homes = {k: int(round(inst.demand[k] * rng.uniform(230, 270))) for k in inst.K}
    inst.social_homes = {k: int(round(inst.homes[k] * rng.uniform(0.2, 0.6))) for k in inst.K}
    inst.hp_cost = {k: round(inst.demand[k] * (HP_BASE + HP_OLD * inst.old[k] + rng.uniform(-6, 6)), 1)
                    for k in inst.K}
    total = sum(inst.demand.values())
    inst.source_name, inst.source_type, inst.open_cost, inst.heat_cost, inst.capacity = {}, {}, {}, {}, {}
    for s, (name, typ, oc, hc, frac) in zip(inst.S, SOURCE_ROLES):
        inst.source_name[s], inst.source_type[s] = name, typ
        inst.open_cost[s] = round(rng.uniform(*oc), 1)
        inst.heat_cost[s] = round(rng.uniform(*hc), 1)
        inst.capacity[s] = int(round(frac * total))

    # data for the low-temperature (LT) vs high-temperature (HT) network question
    inst.lt_pipe_discount = LT_PIPE_DISCOUNT
    inst.booster_cost = {k: round(inst.demand[k] * rng.uniform(3, 5), 1) for k in inst.K}  # at old neighborhoods
    inst.source_booster_cost = {s: round(rng.uniform(60, 90), 1) for s in inst.S if inst.source_type[s] == "LT"}
    inst.social_share_target = float(rng.choice([0.75, 0.8, 0.85]))
    return inst


def one_pipe_example(student_number):
    """Numbers (f, u, d, h) of your personal one-pipe example."""
    rng = np.random.default_rng(personal_seed(student_number, "A1-onepipe"))
    d = int(rng.integers(5, 12))
    u = int(rng.choice([30, 40, 60]))
    f = round(float(rng.uniform(40, 80)), 1)
    h = round(float(rng.uniform(1.05, 1.6) * f), 1)
    return {"f": f, "u": u, "d": d, "h": h}


# ----------------------------------------------------------------------------------------------------------------------
# plotting

def plot_instance(inst, ax=None, title=None, demand=None):
    """Draw the district: streets (gray; main avenues thicker), canals, candidate sources and neighborhoods.
    `demand` (optional): dictionary of demands (MW) to show instead of inst.demand."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 6))
    for (p, q) in inst.canals:
        ax.plot([p[0], q[0]], [p[1], q[1]], color="#7fb3e0", lw=7, alpha=0.6, zorder=0, solid_capstyle="butt")
    for e in inst.E:
        (x1, y1), (x2, y2) = inst.coords[e[0]], inst.coords[e[1]]
        ax.plot([x1, x2], [y1, y2], color="0.75", lw=2.2 if inst.street[e] == "main" else 1.0, zorder=1)
    for n in inst.V:
        if n not in inst.K and n not in inst.S:
            ax.plot(*inst.coords[n], "o", ms=3, color="0.6", zorder=2)
    dem = inst.demand if demand is None else {**inst.demand, **demand}
    box = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75)
    for k in inst.K:
        x, y = inst.coords[k]
        ax.scatter(x, y, s=25 * dem[k], c="#e8a33d" if inst.old[k] else "#69b36b", edgecolors="k", zorder=3)
        ax.annotate(f"{k}: {dem[k]:g} MW", (x, y), textcoords="offset points", xytext=(6, 5), fontsize=7,
                    bbox=box, zorder=6)
    for s in inst.S:
        x, y = inst.coords[s]
        ax.scatter(x, y, s=140, marker="s", c="#c0392b" if inst.source_type[s] == "HT" else "#2e86c1",
                   edgecolors="k", zorder=4)
        ax.annotate(f"{s}: {inst.source_name[s]}", (x, y), textcoords="offset points", xytext=(0, -14), fontsize=7,
                    ha="center", va="top", bbox=box, zorder=6)
    handles = [
        Line2D([], [], marker="o", ls="", mfc="#69b36b", mec="k", label="neighborhood (label B or better)"),
        Line2D([], [], marker="o", ls="", mfc="#e8a33d", mec="k", label="neighborhood (older homes)"),
        Line2D([], [], marker="s", ls="", mfc="#c0392b", mec="k", label="HT source"),
        Line2D([], [], marker="s", ls="", mfc="#2e86c1", mec="k", label="LT source"),
        Line2D([], [], color="#7fb3e0", lw=6, alpha=0.6, label="canal"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3, fontsize=7, frameon=False)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title or repr(inst).split(":")[0], fontsize=9)
    return ax


def plot_design(inst, built_pipes, open_sources, connected, flows=None, ax=None, title=None):
    """Draw a design: built pipes (red, width proportional to flow if `flows` is given), open sources (bold edge)
    and connected neighborhoods (filled; neighborhoods on heat pumps are drawn hollow).

    built_pipes: iterable of pipes (i, j); open_sources: iterable of source nodes; connected: iterable of
    neighborhood nodes; flows (optional): dict {(i, j): flow in MW} on arcs.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 6))
    plot_instance(inst, ax=ax, title=title)
    built = {inst.edge(*e) for e in built_pipes}
    for e in built:
        (x1, y1), (x2, y2) = inst.coords[e[0]], inst.coords[e[1]]
        w = 3.0
        if flows is not None:
            w = 1.0 + 6.0 * (flows.get(e, 0) + flows.get((e[1], e[0]), 0)) / max(inst.pipe_cap.values())
        ax.plot([x1, x2], [y1, y2], color="#c0392b", lw=w, zorder=2.5, alpha=0.85)
    for s in inst.S:
        if s in set(open_sources):
            ax.scatter(*inst.coords[s], s=260, marker="s", facecolors="none", edgecolors="k", lw=2.5, zorder=5)
    for k in inst.K:
        if k not in set(connected):
            ax.scatter(*inst.coords[k], s=25 * inst.demand[k], c="white", edgecolors="k", zorder=3.5)
    return ax
