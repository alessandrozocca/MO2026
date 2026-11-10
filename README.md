# Mathematical Optimization 2026–27

Computer labs and assignment helpers for Mathematical Optimization at Vrije
Universiteit Amsterdam. Teachers: Alessandro Zocca and Rosario Paradiso.

Use the course page on Canvas for lab instructions, deadlines and submission
requirements.

## Assignment 1

The A1 student notebook is distributed separately through Canvas. In Google Colab,
upload that notebook, save a copy in your own Google Drive, and run its Setup cells before
entering your student number. The package supplies your instance generator,
plots and the HiGHS solve helper. Its dependencies include the tested Pyomo and
highspy versions; A1 needs no separate solver executable.

For a local Jupyter environment with Python 3.10 or newer, install:

```bash
python -m pip install "mo2026 @ git+https://github.com/alessandrozocca/MO2026@a1"
```

Use your own student number throughout. Enter a variant suffix only if the
teachers provide one. On a new Colab runtime, rerun Setup.

Before uploading your completed notebook to Canvas, use **Restart and run all**,
run the answer-formatting cell, and save the notebook with all outputs.
`check_answer_format` checks required keys and basic types only.
`print_answer_block` prints a JSON block into the notebook output for the staff
grader. These functions do not check mathematical correctness, save the
notebook or submit it. Upload the `.ipynb` file to Canvas yourself.

## Computer lab setup

Use **Google Colab** for the computer labs. Sign in with your **Google account**,
then use your week's link below.
The link opens a copy dialog. Save a copy in **your own Google Drive** before
editing. You do not need a GitHub account.

| Computer labs in Colab |
|---|
| [Open W1 computer lab notebook in Colab](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%201.ipynb#copy=true) |
| [Open W2 computer lab notebook in Colab](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%202.ipynb#copy=true) |
| [Open W3 computer lab notebook in Colab](https://colab.research.google.com/github/alessandrozocca/MO2026/blob/main/labs/Computer%20exercises%20week%203.ipynb#copy=true) |
| Open W4 computer lab notebook in Colab (coming soon) |
| Open W5 computer lab notebook in Colab (coming soon) |

If the copy dialog does not appear, choose **File → Save a copy in Drive**.
Work in the saved copy; your edits there do not change the course notebook on
GitHub.

Run the cells under **Setup** as provided before starting the exercises. They
prepare the required packages, solvers and course imports automatically.
On a new runtime, allow a minute or more for setup. Wait for the `Week N ready`
message. Ipopt setup may first print `Downloading Ipopt...`; installation logs
are shown only if a stage fails.

Week 2 Exercise 7 has its own setup and can be run independently of Exercises
1–6 and Ipopt. Run the setup and supplied model-builder cells in that exercise.

### If setup fails

- **Restart requested:** restart the session, then rerun both Setup cells and any
  earlier exercise cells needed for your work.
- **Connection error:** check your connection and rerun the failed
  setup cell once connectivity is restored.
- **New Colab runtime:** run Setup again; installed packages and temporary files
  do not carry over to a new runtime.

Bring questions about the exercises, setup or troubleshooting to the **weekly
computer labs**. For errors, have your notebook and the full error message ready.

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

You can download your saved Colab copy using **File → Download → Download .ipynb**,
then open it in Jupyter and run its Setup cells. These still download course
helpers, so internet access is required. Outside Colab, setup reports missing
Python dependencies instead of installing them automatically. In W2, plotting
and data work remain available without Ipopt; nonlinear solve cells explain how
to install it when needed.

On a python.org installation for macOS, an SSL certificate error may mean that
the bundled **Install Certificates.command** has not been run. Run it from the
Python folder in Applications, then rerun Setup. Keep certificate verification
enabled.
