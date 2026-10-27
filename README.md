# Mathematical Optimization course 2026–27

Helper functions for the Mathematical Optimization course at Vrije Universiteit Amsterdam.
Teachers: Alessandro Zocca and Rosario Paradiso. Use the current course page on Canvas for deadlines,
TA contacts and submission instructions.

## Current layout

The helpers are currently ordinary Python modules in this directory:

- `installer.py`: setup and readiness checks for the course solver stack;
- `tutorial1.py`: graph/network drawings and side-by-side dataframe display;
- `tutorial2.py`: feasible-region and objective plots;
- `tutorial3.py`: attaching and displaying constraint duals.

Run from a checkout of this directory, or add it to the notebook's Python import path. This checkout has no
package metadata yet. The planned `mo2026` package, reviewed `common.py` and immutable lab release tag are
separate migration steps; a `pip install` of this Git repository is not the current installation method.
Pin a reviewed commit or tag when preparing the 2026 notebook setup cells.

## Python dependencies

Activate the environment used by your local notebook and install:

```bash
python -m pip install "pyomo==6.10.1" "highspy==1.15.1" numpy pandas matplotlib networkx sympy scipy scikit-learn ipython jinja2
```

In Colab, use `%pip` in the notebook kernel for the same dependencies:

```python
%pip install "pyomo==6.10.1" "highspy==1.15.1" numpy pandas matplotlib networkx sympy scipy scikit-learn ipython jinja2
```

Restart the kernel if an already-imported package was changed. Jinja2 supplies the optional pandas Styler
HTML display support. Importing these helpers does not install packages or download solvers.

From this checkout, check the LP/MILP environment with:

```python
import installer
print(installer.check_solvers())
```

This verifies the pinned versions, solves a known LP, checks its indexed duals, and checks that a second LP
is infeasible. `installer.install_pyomo()` and `installer.install_highs()` are optional checked installers
for the two pinned packages; they use the active Python interpreter and propagate installation failures.

## Ipopt for nonlinear models

HiGHS through the course's `appsi_highs` interface handles LP/MILP models. Use a separate Ipopt executable
for the nonlinear examples. Installing Pyomo or highspy does not install that executable.

For a local environment, install Ipopt separately and put it on PATH; one option is
`conda install -c conda-forge ipopt` in the notebook's environment. See the
[Ipopt installation documentation](https://coin-or.github.io/Ipopt/INSTALL.html).
`installer.install_ipopt()` verifies an existing executable and raises with instructions if it is missing locally.

On Colab, after installing the Python dependencies and making these modules available, run:

```python
import installer
installer.install_ipopt()
print(installer.check_solvers(include_ipopt=True))
```

If Ipopt is missing on Colab, the helper installs `idaes-pse==2.13.0` with the course Pyomo/HiGHS pins,
then downloads IDAES binary release `3.4.2` into `./bin`. It checks the command result and the downloaded
Ipopt executable before adding that directory to PATH. The same download can be explicitly requested locally
with `installer.install_idaes_solvers(destination="./bin")`; platform/download errors propagate.
See [IDAES binary installation options](https://idaes-pse.readthedocs.io/en/latest/reference_guides/commands/get_extensions.html).

The old catalog of CBC, CPLEX and other solver installers has been retired. The revised 2026 week-1
notebook uses HiGHS and pins its drawing helpers to published commit `2d08a49`. Week 2 uses Ipopt for
its nonlinear models and pins `installer.py` and `tutorial2.py` to published commit `41c99bd`. Both
notebook setups check downloaded helper checksums and also support a local checkout. Week 3 uses
HiGHS for its LPs and Ipopt for its quadratic primal/dual, pinning `installer.py` and `tutorial3.py`
to published commit `07c07eb`. It teaches direct suffix access and preserves raw row-dual signs.
The notebooks are maintained in the staff course folder; weeks 4–5 still await their planned revision.

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

## Verification and release status

The helper checks use the course's Pyomo 6.10.1 and highspy 1.15.1 pins. Local verification uses Python 3.13.14
and Ipopt 3.14.20. The installer failure cases are checked with mocked commands; a fresh Colab installation and
“Restart and run all” remain release checks. IDAES binary downloads have not been claimed as tested on Colab.

Keep this repository at the helper-only stage until the scheduled assignment releases. Add A1 instance support
for 11 November; add A2 support/data only after the A1 deadline on 23 November, for the 25 November release.
Staff solutions, reference models and graders belong in the staff course folder.
