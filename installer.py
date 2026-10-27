"""Setup and readiness checks for the MO 2026 course solver stack.

Python package installs use the active interpreter. Ipopt is a separate executable;
IDAES binaries are downloaded only on Colab or by an explicit call to
``install_idaes_solvers``. No installation runs when this module is imported.
"""

import importlib
from importlib import metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys

PYOMO_VERSION = "6.10.1"
HIGHSPY_VERSION = "1.15.1"
IDAES_VERSION = "2.13.0"
IDAES_BINARY_RELEASE = "3.4.2"


def _has_executable(executable_name):
    """Check PATH or an explicit path, including execute permissions."""
    return executable_name is None or shutil.which(os.fspath(executable_name)) is not None


def _has_module(module_name):
    if module_name is None:
        return True
    try:
        importlib.import_module(module_name)
    except ImportError:
        return False
    return True


def _check_available(executable, module):
    return _has_executable(executable) and _has_module(module)


def found_installation(executable=None, module=None):
    """Check presence; package version checks are done by the install functions."""
    if executable is None and module is None:
        raise ValueError("Specify an executable or a module.")
    available = _check_available(executable, module)
    if available:
        print(f"{executable or module} was previously installed")
    return available


def confirm_installation(executable=None, module=None):
    if executable is None and module is None:
        raise ValueError("Specify an executable or a module.")
    available = _check_available(executable, module)
    print("installation successful" if available else "installation failed")
    return available


def on_colab():
    return "google.colab" in sys.modules


def _version(distribution):
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _install_package(distribution, module, version, extra_requirements=()):
    if _version(distribution) == version and _has_module(module):
        print(f"{distribution} {version} was previously installed")
        return True
    was_loaded = module in sys.modules
    subprocess.run(
        [sys.executable, "-m", "pip", "install", f"{distribution}=={version}", *extra_requirements],
        check=True,
    )
    importlib.invalidate_caches()
    if _version(distribution) != version:
        raise RuntimeError(f"Installation did not provide {distribution} {version}.")
    if was_loaded:
        raise RuntimeError(
            f"{distribution} was changed after import. Restart the kernel, then rerun setup."
        )
    if not _has_module(module):
        raise RuntimeError(f"{distribution} was installed but {module} cannot be imported.")
    return True


def install_pyomo():
    return _install_package("pyomo", "pyomo", PYOMO_VERSION)


def install_highs():
    return _install_package("highspy", "highspy", HIGHSPY_VERSION)


def install_idaes():
    """Install the pinned IDAES command without relaxing the course solver pins."""
    install_pyomo()
    install_highs()
    return _install_package(
        "idaes-pse", "idaes", IDAES_VERSION,
        (f"pyomo=={PYOMO_VERSION}", f"highspy=={HIGHSPY_VERSION}"),
    )


def _verify_ipopt(executable="ipopt"):
    path = shutil.which(os.fspath(executable))
    if path is None:
        raise RuntimeError(f"No executable Ipopt found at {executable!s}. See README.md.")
    result = subprocess.run([path, "-v"], check=True, capture_output=True, text=True)
    version = (result.stdout + result.stderr).strip()
    if "ipopt" not in version.lower():
        raise RuntimeError(f"{path} did not identify itself as Ipopt.")
    return version.splitlines()[0]


def install_idaes_solvers(destination=None):
    """Download a fixed IDAES binary release and verify Ipopt in that directory.

    The default destination is ``./bin``; system installation directories are not
    modified. Unsupported platforms, failed downloads and unusable binaries raise.
    """
    if not install_idaes():
        raise RuntimeError("IDAES installation failed; solver download was not attempted.")
    destination = Path(destination or Path.cwd() / "bin").expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    # Invoke the console entry point in the active interpreter, not another
    # environment's `idaes` executable found on PATH.
    subprocess.run(
        [sys.executable, "-c", "from idaes.commands.base import command_base; command_base()",
         "get-extensions", "--release", IDAES_BINARY_RELEASE, "--to", str(destination)],
        check=True,
    )
    executable = destination / ("ipopt.exe" if os.name == "nt" else "ipopt")
    _verify_ipopt(executable)
    paths = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join([str(destination), *[p for p in paths if p != str(destination)]])
    return True


def install_ipopt(destination=None):
    """Verify existing Ipopt; on Colab download IDAES binaries if it is missing.

    Outside Colab, install Ipopt separately (README), or explicitly call
    ``install_idaes_solvers`` to request an IDAES binary download.
    """
    if destination is None and _has_executable("ipopt"):
        print(_verify_ipopt())
        return True
    if on_colab() or destination is not None:
        return install_idaes_solvers(destination)
    raise RuntimeError(
        "Ipopt is not on PATH. Install the Ipopt executable separately (see README.md), "
        "or explicitly call install_idaes_solvers() for the IDAES binary distribution."
    )


def check_solvers(include_ipopt=False):
    """Run small independent checks; do not install or change any packages."""
    for distribution, expected in [("pyomo", PYOMO_VERSION), ("highspy", HIGHSPY_VERSION)]:
        if _version(distribution) != expected:
            raise RuntimeError(f"Expected {distribution} {expected}; rerun setup before this check.")
    import pyomo.environ as pyo

    solver = pyo.SolverFactory("appsi_highs")
    if not solver.available(exception_flag=False):
        raise RuntimeError("The appsi_highs solver is unavailable.")
    model = pyo.ConcreteModel()
    model.x = pyo.Var([1, 2], domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint([1, 2], rule=lambda m, i: m.x[i] >= i)
    model.objective = pyo.Objective(expr=sum(model.x[i] for i in [1, 2]))
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    result = solver.solve(model)
    if not pyo.check_optimal_termination(result) or abs(pyo.value(model.objective) - 3) > 1e-7:
        raise RuntimeError("HiGHS did not solve the known LP correctly.")
    duals = [model.dual[model.c[i]] for i in [1, 2]]
    if any(abs(v - 1) > 1e-7 for v in duals):
        raise RuntimeError("Indexed LP duals were not imported correctly.")

    infeasible = pyo.ConcreteModel()
    infeasible.x = pyo.Var(bounds=(0, 1))
    infeasible.c = pyo.Constraint(expr=infeasible.x >= 2)
    infeasible.objective = pyo.Objective(expr=infeasible.x)
    result = solver.solve(infeasible, load_solutions=False)
    if result.solver.termination_condition != pyo.TerminationCondition.infeasible:
        raise RuntimeError("HiGHS did not identify the known infeasible LP.")
    report = {"pyomo": PYOMO_VERSION, "highspy": HIGHSPY_VERSION,
              "lp_objective": pyo.value(model.objective), "indexed_duals": duals,
              "infeasible_status": "infeasible"}
    if include_ipopt:
        report["ipopt"] = _verify_ipopt()
        nlp = pyo.ConcreteModel()
        nlp.x = pyo.Var(initialize=0)
        nlp.objective = pyo.Objective(expr=(nlp.x - 2) ** 2)
        result = pyo.SolverFactory("ipopt").solve(nlp)
        if not pyo.check_optimal_termination(result) or abs(pyo.value(nlp.x) - 2) > 1e-6:
            raise RuntimeError("Ipopt did not solve the known convex quadratic correctly.")
        report["nlp_solution"] = pyo.value(nlp.x)
    return report
