# Mathematical Optimization 2026–27

Computer labs and Python helpers for Mathematical Optimization at Vrije
Universiteit Amsterdam. Teachers: Alessandro Zocca and Rosario Paradiso.

Use the course page on Canvas for lab instructions, deadlines, TA contacts and
submission requirements.

## Computer lab setup

Open your week's notebook in Google Colab and save your own copy before editing.

| Notebook | Open in Colab |
|---|---|
| [Week 1: linear and integer optimization](labs/Computer%20exercises%20week%201.ipynb) | [Open](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%201.ipynb) |
| [Week 2: convex and nonlinear optimization](labs/Computer%20exercises%20week%202.ipynb) | [Open](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%202.ipynb) |
| [Week 3: duality](labs/Computer%20exercises%20week%203.ipynb) | [Open](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%203.ipynb) |

Run the two cells under **Setup** before starting the exercises. On Colab, they
prepare the required packages, solvers and course helpers automatically. The
first cell may appear collapsed; expand it if you want to read its code. You do
not need to clone this repository, mount Google Drive or install this repository
as a package.

Week 2 Exercise 7 has its own setup and can be run independently of Exercises
1–6 and Ipopt. Run the setup and supplied model-builder cells in that exercise.

### If setup fails

- **Restart requested:** restart the session, then rerun both Setup cells and any
  earlier exercise cells needed for your work.
- **Download or connection error:** check your connection and rerun the failed
  setup cell once connectivity is restored.
- **New Colab runtime:** run Setup again; installed packages and temporary files
  do not carry over to a new runtime.
- **Persistent error:** give a TA the full error message and identify the notebook
  and cell where it occurred.

### Running locally (optional)

Use Python 3.10 or newer. Install the following packages in the Python environment
used by your notebook:

```bash
python -m pip install "pyomo==6.10.1" "highspy==1.15.1" numpy pandas matplotlib networkx sympy scipy scikit-learn ipython jinja2
```

Weeks 2 (Exercises 1–6) and 3 also require the separate Ipopt executable on PATH.
If you use conda, one installation option is:

```bash
conda install -c conda-forge ipopt
```

See the [Ipopt installation documentation](https://coin-or.github.io/Ipopt/INSTALL.html)
for other options. Pyomo and highspy do not supply Ipopt.

Download your notebook from [labs/](labs/) and run its Setup cells. These still
download course helpers, so internet access is required. Outside Colab, setup
reports missing dependencies instead of installing them automatically.
