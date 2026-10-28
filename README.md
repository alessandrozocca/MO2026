# Mathematical Optimization course 2026–27

Helper functions for the Mathematical Optimization course at Vrije Universiteit Amsterdam.
Teachers: Alessandro Zocca and Rosario Paradiso. Use the current course page on Canvas for deadlines,
TA contacts and submission instructions.

## Computer lab setup

For the revised W1–W3 Colab notebooks, run the two setup cells before starting.
The first cell is displayed as a form; expand it to inspect the source. It loads
`lab_setup.py` from a fixed public commit, checks its SHA-256 checksum before
execution, then calls `setup(week=..., check=False, verbose=False)`. No Drive mount, GitHub login, repository
clone or package installation of this repository is needed.

The course modules remain ordinary Python files:

- `lab_setup.py`: package checks, verified helper downloads and solver preparation;
- `installer.py`: the existing solver installer and standalone readiness checks;
- `tutorial1.py`: graph/network drawings and side-by-side dataframe display;
- `tutorial2.py`: feasible-region and objective plots;
- `tutorial3.py`: attaching and displaying constraint duals.

The setup module imports only the Python standard library. Importing it does not
install packages, download files, change the Python import path or run solvers.
An explicit `setup(...)` call performs those operations and returns named objects;
it does not insert notebook variables, seed random generators or load datasets.

```python
import lab_setup  # when this file is already available locally
lab = lab_setup.setup(week=3)
lp_solver, nlp_solver = lab.lp_solver, lab.nlp_solver
add_dual_variables = lab.helpers["tutorial3"].add_dual_variables
```

| Week | Default interfaces | Additional packages and course helpers |
|---|---|---|
| 1 | HiGHS (`appsi_highs`) | Matplotlib, NetworkX, SciPy; `tutorial1` |
| 2 | Ipopt | Matplotlib, SymPy, SciPy, scikit-learn; `tutorial2` |
| 3 | HiGHS and Ipopt | `tutorial3` |
| 4 preparation | HiGHS | Matplotlib, SciPy |
| 5 preparation | HiGHS and Ipopt | Matplotlib, SciPy, Requests |

Every profile also checks Pyomo 6.10.1, highspy 1.15.1, NumPy, pandas, IPython
and Jinja2. The latter provides pandas Styler HTML support. Installation is
permitted by default on Colab and disabled elsewhere. Compatible installed
packages are reused. If installation changes a package already imported into
the session, setup stops and asks for a kernel restart; rerun Setup afterwards.

Python 3.10 or newer is required. HiGHS handles LP/MILP models. Ipopt handles
smooth continuous nonlinear models and does not certify global optimality for
nonconvex problems. It is a separate executable, not supplied by Pyomo or highspy.
When needed, setup reuses a verified existing executable or, on Colab, requests
`idaes-pse==2.13.0` and IDAES binary release `3.4.2` through the course installer.
Downloaded executables are stored in a temporary course cache and checked before
they are added to PATH. IDAES checksums remain enabled. Platform/download errors
stop setup. See the [IDAES binary installation options](https://idaes-pse.readthedocs.io/en/stable/reference_guides/commands/get_extensions.html).

Course helper files are downloaded from public commit `07c07eb` and checked
against fixed SHA-256 values. Cache files are verified before reuse; invalid
files are downloaded again and verified before replacement. Network timeouts
and transient failures have bounded retries. New Colab runtimes need to recreate
the environment because their temporary files and installations do not persist.
The notebook's small initial loader retrieves `lab_setup.py` on each run; if that
request fails, rerun the setup cell once connectivity is restored.

Student notebook setup checks package versions and solver availability without
running staff test models or printing diagnostic reports. Staff can explicitly
request `check=True` to solve a small LP with indexed duals, a known infeasible LP
for HiGHS, and a convex quadratic for Ipopt, and use `verbose=True` for versions
and helper provenance. A failed stage retains its original exception and installation
log. These checks establish readiness, not correctness of an exercise model.

### Local notebooks and development

Install the packages once in the environment running your notebook:

```bash
python -m pip install "pyomo==6.10.1" "highspy==1.15.1" numpy pandas matplotlib networkx sympy scipy scikit-learn ipython jinja2
```

For W2/W3, install Ipopt separately on PATH; one option is
`conda install -c conda-forge ipopt`. See the
[Ipopt installation documentation](https://coin-or.github.io/Ipopt/INSTALL.html).
Missing packages or Ipopt raise instructions locally instead of installing them.
An explicit `setup(..., install=True)` permits both package installation and the
course binary download; `install=False` disables both, including on Colab.

To test editable helpers, set `MO2026_REPO` before starting Jupyter:

```bash
export MO2026_REPO="/path/to/MO2026"
jupyter lab
```

Use the directory containing `lab_setup.py`, `installer.py` and `tutorial*.py`.
The notebook then reads these local files without applying public checksums.
The `local_repo=` argument to `setup` controls supporting helper files when the
setup module has already been imported. Use absolute paths; a changed working
directory does not change the course cache or a resolved helper directory.

### Solving and reporting

`solve_and_load(model, solver)` checks optimal termination before loading a
solution. W1 shows these steps next to its first LP, rather than in Setup.
For LP/MILP experiments, `solve(model, options=...)` returns a dictionary with
`status`, `objective`, `bound`, `gap`, `nodes` and `time`. The helper loads only
an available feasible solution; an absent incumbent is reported as `None`.
An `optimal` status certifies an optimum. A limited solve can return `other`
while providing an incumbent and a valid bound. Check status before interpreting
values; `gap` is a fraction and `bound` is the processed solver bound, not a
separately solved plain LP value. `relax_integrality(model)` relaxes every integer
domain in place. Use fresh models for LP, root-limited and full MILP comparisons.

W1 covers shipping visit inequalities and aggregated/individual facility links.
W2 adds independent OLS evaluation and a coordination surcharge with isolated
product tests. W2 Exercise 7 has its own collapsed HiGHS setup and supplied base
builder: run those cells to work on it independently of Exercises 1–6 and Ipopt.
Visible Setup code contains scientific imports and symbolic plotting variables;
helper loading, formatting and staff diagnostics stay out of the student flow.

### Future lab requirements

W4/W5 preparation profiles do not modernize or validate the legacy notebooks.
The legacy W5 CPLEX interface is not installed automatically, and Ipopt is not
a substitute for a dedicated conic solver. A revised notebook can select its
interfaces explicitly, add Python dependencies, and configure solver options:

```python
lab = lab_setup.setup(
    week=5,
    solvers=("appsi_highs", "ipopt"),
    extra_packages=("sympy",),
    solver_options={"ipopt": {"tol": 1e-8}},
)
```

`extra_packages` accepts distribution names or exact version pins and cannot
replace the course solver pins. Other Pyomo interfaces can be selected, but
their packages, executables and licenses must be supplied separately. Additional
interfaces receive an availability check; the built-in solve checks apply only
to HiGHS and Ipopt. Solver capabilities and mathematical reformulations remain
explicit choices in the notebook. No statistical sampling or data manipulation
belongs in the setup module.

## Helper conventions

```python
from tutorial1 import draw_graph, draw_network, display_side_by_side
from tutorial2 import plot_feasible_region, plot_objective, generateinstance
from tutorial3 import add_dual_variables, display_dual_variables
```

- Graphs draw every declared node, including isolated nodes. Node IDs can be strings or numbers; colors follow
  declared node order. `node_labels`, when supplied to `draw_graph`, uses the existing single-letter labels.
- `draw_network` retains the simple directed-network format: edge keys are unique `(source, target)` pairs.
  Week 1 retains the simple 17-arc second network: its single `(3, 4)` arc has capacity 10 and cost 3.
  A parallel-arc model and drawing would require a separate arc-ID format.
- `display_side_by_side` accepts repeated captions and requires one caption per dataframe.
- `plot_objective` uses the plot's actual axis variables, independently of their display labels. A multivariable
  objective needs explicit level values. An empty level list raises a clear error.
- `generateinstance(m, n, seed)` is retained for compatibility with the 2025 notebooks; revised week 2 no longer
  imports it. It requires positive integer dimensions with `m >= n`, checks full column rank without forming
  a Gram matrix, and has bounded retries.
- Attach the dual suffix before a continuous solve and display duals only after a successful solve. The display
  helper handles indexed constraints and active nested blocks. It shows the original row and the **raw RHS dual**;
  missing duals are reported as unavailable. For minimization written as `g(x) <= b`, the textbook multiplier in
  `L = f + lambda * (g - b)` is minus that raw dual. At a kink it is a supporting slope, not necessarily a unique
  derivative. Integer models require fixing the design and solving a continuous model before interpreting LP duals.

## Verification status

Local verification uses Python 3.13.14, Pyomo 6.10.1, highspy 1.15.1 and Ipopt
3.14.20. Checks cover import isolation, checksum failures, cached and local
helpers, repeated setup, package/restart failure paths, solver options and actual
solver calls. A fresh hosted Colab installation and session restart remain
separate release checks; mocked installation tests are not evidence of a
successful IDAES binary download on Colab.
