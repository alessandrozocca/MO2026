"""Prepare the Python helpers and solvers for the MO 2026 computer labs.

Importing this module uses only the standard library and performs no downloads,
installations, solver calls or changes to the import path. Call ``setup(week)``
explicitly. Installation defaults to enabled on Colab and disabled elsewhere.

Weeks 4 and 5 provide preparation profiles for future notebook revisions. The
legacy week-5 CPLEX interface is not installed or replaced automatically. Select
additional Pyomo solver interfaces explicitly with ``solvers=...``; their Python
packages, executables and licenses must be supplied separately.
"""

from __future__ import annotations

import hashlib
import importlib
from importlib import metadata, util
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

API_VERSION = 1
PYOMO_VERSION = "6.10.1"
HIGHSPY_VERSION = "1.15.1"

# All four files have these bytes in this existing public revision.
HELPER_COMMIT = "07c07ebb7c35ba0fba7811b91ee880ce4678cf19"
HELPER_SHA256 = {
    "installer": "532519605a3c1386b87fc7714fe9836e3dc788760867e5e9d1d72ebce4325323",
    "tutorial1": "7443f6376ac34d7d84f738df5686d9dd42dbc73063f391f1ac657a646daa1e5a",
    "tutorial2": "a67b1641926d73e8ad600ccf286c377c1ebe1f58ab2adce32ea43f1ffccfb8d1",
    "tutorial3": "17d4aaf1f6e214db88c8c357ac933cd9f6552e602b5dbfa4dfb5a9eed6d3875b",
}
_RAW_ROOT = f"https://raw.githubusercontent.com/alessandrozocca/MO2026/{HELPER_COMMIT}"
_IMPORT_NAMES = {"scikit-learn": "sklearn", "ipython": "IPython", "idaes-pse": "idaes"}
_BASE_PACKAGES = (f"pyomo=={PYOMO_VERSION}", f"highspy=={HIGHSPY_VERSION}",
                  "numpy", "pandas", "ipython", "jinja2")

# Each profile contains infrastructure requirements, not models or datasets.
PROFILES = {
    1: {"packages": ("matplotlib", "networkx", "scipy"),
        "helpers": ("tutorial1",), "solvers": ("appsi_highs",)},
    2: {"packages": ("matplotlib", "sympy", "scipy", "scikit-learn"),
        "helpers": ("tutorial2",), "solvers": ("ipopt",)},
    3: {"packages": (), "helpers": ("tutorial3",),
        "solvers": ("appsi_highs", "ipopt")},
    4: {"packages": ("matplotlib", "scipy"), "helpers": (),
        "solvers": ("appsi_highs",)},
    5: {"packages": ("matplotlib", "scipy", "requests"), "helpers": (),
        "solvers": ("appsi_highs", "ipopt")},
}


class SetupError(RuntimeError):
    """A setup stage failed; the original exception is retained as its cause."""


class LabEnvironment(SimpleNamespace):
    """Explicit results of setup: ``solvers``, ``helpers`` and ``versions``.

    ``lp_solver`` and ``nlp_solver`` are conveniences for the course interfaces.
    A solver that was not requested has value ``None``. No notebook globals are
    inserted, no random seed is changed, and no exercise model is constructed.
    """

    @property
    def lp_solver(self):
        return self.solvers.get("appsi_highs")

    @property
    def nlp_solver(self):
        return self.solvers.get("ipopt")


def on_colab():
    return "google.colab" in sys.modules


def _version(distribution):
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _requirements(week, extra_packages):
    if isinstance(week, bool) or not isinstance(week, int) or week not in PROFILES:
        raise ValueError("week must be an integer from 1 to 5")
    if isinstance(extra_packages, str):
        raise ValueError("extra_packages must be a sequence, not a single string")
    requirements = {}
    for requirement in (*_BASE_PACKAGES, *PROFILES[week]["packages"], *extra_packages):
        # A deliberately small interface: a distribution name or an exact pin.
        # Arguments, URLs and shell fragments are not package requirements here.
        if not isinstance(requirement, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:==[A-Za-z0-9][A-Za-z0-9_.+!-]*)?", requirement):
            raise ValueError(f"Use a package name or an exact version pin: {requirement!r}")
        name, _, expected = requirement.partition("==")
        name = re.sub(r"[-_.]+", "-", name).lower()
        previous = requirements.get(name)
        if previous and expected and previous != expected:
            raise ValueError(f"Conflicting version pins for {name}")
        requirements[name] = expected or previous
    return requirements


def _loaded_versions(versions):
    return {name: installed for name, installed in versions.items()
            if _IMPORT_NAMES.get(name, name.replace("-", "_")) in sys.modules}


def _check_restart(loaded):
    changed = [name for name, installed in loaded.items() if installed != _version(name)]
    if changed:
        raise SetupError("Packages changed after import: " + ", ".join(sorted(changed))
                         + ". Restart the kernel, then rerun Setup before other cells.")


def _prepare_packages(requirements, install):
    before = {name: _version(name) for name in requirements}
    missing = [name for name, expected in requirements.items()
               if before[name] is None or (expected and before[name] != expected)]
    command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
               *[name + (f"=={expected}" if expected else "")
                 for name, expected in requirements.items()]]
    if missing:
        if not install:
            raise SetupError("Missing or incompatible packages: " + ", ".join(missing)
                             + ". Install them in this notebook's environment with:\n"
                             + " ".join(command) + "\nThen restart the kernel and rerun Setup.")
        loaded = _loaded_versions(before)
        # Capture successful pip output; retain the complete log on failure.
        subprocess.run(command, check=True, capture_output=True, text=True)
        importlib.invalidate_caches()
        _check_restart(loaded)
    versions = {name: _version(name) for name in requirements}
    for name, expected in requirements.items():
        if versions[name] is None or (expected and versions[name] != expected):
            raise SetupError(f"Installation did not provide {name}"
                             + (f"=={expected}" if expected else "") + ".")
    return versions


def _download(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
        time.sleep(0.5 * (attempt + 1))


def _helper_path(name, cache, local_repo):
    if name not in HELPER_SHA256:
        raise ValueError(f"Unknown course helper: {name}")
    if local_repo is not None:
        path = local_repo / f"{name}.py"
        if not path.is_file():
            raise SetupError(f"The local helper directory does not contain {name}.py: {local_repo}")
        return path
    path = cache / HELPER_COMMIT / f"{name}.py"
    expected = HELPER_SHA256[name]
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return path
    source = _download(f"{_RAW_ROOT}/{name}.py")
    if hashlib.sha256(source).hexdigest() != expected:
        raise SetupError(f"Checksum mismatch for {name}.py; the download was not executed.")
    path.parent.mkdir(parents=True, exist_ok=True)
    # A failed or interrupted write must not replace a verified cached file.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(source)
            stream.flush()
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _load_helper(name, cache, local_repo):
    path = _helper_path(name, cache, local_repo)
    source = path.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    # Check again before execution, including a file replaced during the read.
    if local_repo is None and digest != HELPER_SHA256[name]:
        raise SetupError(f"Checksum mismatch for cached {name}.py; the file was not executed.")
    module_name = f"_mo2026_{name}_{digest}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = util.spec_from_file_location(module_name, path)
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        # Execute the exact verified bytes, without reusing an old .pyc file.
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def _prepare_ipopt(installer, cache, install, optional=False):
    if shutil.which("ipopt"):
        return installer._verify_ipopt()
    destination = cache / f"ipopt-{installer.IDAES_BINARY_RELEASE}"
    executable = destination / ("ipopt.exe" if os.name == "nt" else "ipopt")
    if not executable.is_file():
        if not install:
            if optional:
                return None
            raise SetupError("Ipopt is not on PATH. Install its separate executable, "
                             "or explicitly use setup(..., install=True) to request the course binary download.")
        _prepare_packages({"idaes-pse": installer.IDAES_VERSION,
                           "pyomo": PYOMO_VERSION, "highspy": HIGHSPY_VERSION}, True)
        destination.mkdir(parents=True, exist_ok=True)
        print("Downloading Ipopt...")
        subprocess.run(
            [sys.executable, "-c", "from idaes.commands.base import command_base; command_base()",
             "get-extensions", "--release", installer.IDAES_BINARY_RELEASE, "--to", str(destination)],
            check=True, capture_output=True, text=True,
        )
    description = installer._verify_ipopt(executable)
    entries = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join([str(destination), *[p for p in entries if p != str(destination)]])
    return description


def _check_solver(pyo, name, solver):
    """Check interface behavior, including LP duals and infeasible termination."""
    if name == "appsi_highs":
        model = pyo.ConcreteModel()
        model.x = pyo.Var([1, 2], domain=pyo.NonNegativeReals)
        model.row = pyo.Constraint([1, 2], rule=lambda m, k: m.x[k] >= k)
        model.obj = pyo.Objective(expr=sum(model.x[k] for k in (1, 2)))
        model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
        result = solver.solve(model, load_solutions=False)
        pyo.assert_optimal_termination(result)
        model.solutions.load_from(result)
        values = [pyo.value(model.obj), *[model.dual[model.row[k]] for k in (1, 2)]]
        if not all(math.isfinite(value) for value in values) or any(
                abs(value - expected) > 1e-7 for value, expected in zip(values, (3, 1, 1))):
            raise SetupError("HiGHS failed the LP objective/dual check.")
        bad = pyo.ConcreteModel()
        bad.x = pyo.Var(bounds=(0, 1))
        bad.row = pyo.Constraint(expr=bad.x >= 2)
        bad.obj = pyo.Objective(expr=bad.x)
        result = solver.solve(bad, load_solutions=False)
        if result.solver.termination_condition != pyo.TerminationCondition.infeasible:
            raise SetupError("HiGHS failed the infeasibility check.")
    elif name == "ipopt":
        model = pyo.ConcreteModel()
        model.x = pyo.Var(initialize=0)
        model.obj = pyo.Objective(expr=(model.x - 2)**2)
        result = solver.solve(model, load_solutions=False)
        pyo.assert_optimal_termination(result)
        model.solutions.load_from(result)
        value = pyo.value(model.x)
        if not math.isfinite(value) or abs(value - 2) > 1e-6:
            raise SetupError("Ipopt failed the convex quadratic check.")


def setup(week, *, install=None, solvers=None, extra_packages=(), solver_options=None,
          local_repo=None, cache_dir=None, check=True, verbose=True, optional_ipopt=False):
    """Return a prepared ``LabEnvironment`` for a week from 1 to 5.

    ``install=None`` permits installation only on Colab. ``install=False`` never
    installs packages or solver binaries; ``install=True`` explicitly permits
    both. Package installation uses the running interpreter. Course helpers are
    downloaded and verified even when installation is disabled.

    ``solvers`` overrides the profile's tuple of Pyomo interface names. Options
    are passed as ``solver_options={"ipopt": {"tol": 1e-9}}``. Additional solver
    interfaces are checked for availability but have no generic solve test.
    In particular, selecting Ipopt does not provide a conic solver or a global
    optimality certificate for a nonconvex problem.

    ``extra_packages`` accepts distribution names or exact ``name==version``
    pins, without overriding the course solver pins. ``local_repo`` (or the
    staff environment variable ``MO2026_REPO``) reads editable helper files from
    that directory without public checksums. Cache paths are absolute and do
    not depend on the notebook's current working directory.

    ``optional_ipopt=True`` permits plotting/data work when Ipopt is absent and
    installation is disabled. Then ``nlp_solver`` is None. Installation failures
    and unusable existing/cached binaries still raise. Other solvers and package
    requirements are unchanged.
    """
    if sys.version_info < (3, 10):
        raise SetupError("The computer lab helpers require Python 3.10 or newer.")
    requirements = _requirements(week, extra_packages)
    if install is not None and not isinstance(install, bool):
        raise ValueError("install must be True, False or None")
    if not isinstance(optional_ipopt, bool):
        raise ValueError("optional_ipopt must be True or False")
    install = on_colab() if install is None else install
    names = PROFILES[week]["solvers"] if solvers is None else solvers
    if not isinstance(names, (tuple, list)) or not names or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) for name in names):
        raise ValueError("solvers must be a nonempty sequence of Pyomo interface names")
    if len(set(names)) != len(names):
        raise ValueError("Duplicate solver interfaces")
    options = {} if solver_options is None else solver_options
    if not isinstance(options, dict) or set(options) - set(names) or any(
            not isinstance(value, dict) for value in options.values()):
        raise ValueError("solver_options must map requested solver names to option dictionaries")
    local = local_repo if local_repo is not None else os.environ.get("MO2026_REPO")
    local = Path(local).expanduser().resolve() if local else None
    if local is not None and not local.is_dir():
        raise SetupError(f"The local helper directory does not exist: {local}")
    cache = Path(cache_dir or Path(tempfile.gettempdir()) / "mo2026-labs").expanduser().resolve()
    stage = "Python packages"
    try:
        versions = _prepare_packages(requirements, install)
        stage = "Ipopt executable"
        if "ipopt" in names:
            loaded = _loaded_versions(versions)
            installer = _load_helper("installer", cache, local)
            versions["ipopt"] = _prepare_ipopt(installer, cache, install, optional_ipopt)
            # IDAES may install dependencies too. Check loaded versions and pins
            # before importing plotting/dual helpers or reporting readiness.
            _check_restart(loaded)
            versions.update(_prepare_packages(requirements, False))
        stage = "course helpers"
        helpers = {name: _load_helper(name, cache, local) for name in PROFILES[week]["helpers"]}
        stage = "solver interfaces"
        import pyomo.environ as pyo
        prepared = {}
        for name in names:
            if name == "ipopt" and versions.get("ipopt") is None:
                continue
            stage = f"{name} solver interface"
            solver = pyo.SolverFactory(name)
            if not solver.available(exception_flag=False):
                raise SetupError(f"Solver interface {name!r} is unavailable. "
                                 "Its required Python package/executable and any license must be installed separately.")
            if name == "ipopt":
                solver.options.update({"tol": 1e-9, "bound_relax_factor": 0})
            solver.options.update(options.get(name, {}))
            if check:
                stage = f"{name} readiness check"
                _check_solver(pyo, name, solver)
            prepared[name] = solver
        source = f"local helpers: {local}" if local else f"public helpers: {HELPER_COMMIT[:7]}"
        environment = LabEnvironment(week=week, solvers=prepared, helpers=helpers,
                                     versions=versions, source=source, checks_run=bool(check))
        if verbose:
            if "ipopt" in names and environment.nlp_solver is None:
                print(f"Week {week} ready for plotting and data work; Ipopt is unavailable. "
                      "Install its separate executable before running nonlinear solve cells.")
            else:
                descriptions = [f"HiGHS {versions['highspy']}" if name == "appsi_highs"
                                else versions.get(name, name) for name in names]
                print(f"Week {week} ready: Pyomo {versions['pyomo']}; "
                      + "; ".join(descriptions) + ".")
        return environment
    except Exception as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            detail += "\n" + (exc.stdout or "") + (exc.stderr or "")
        raise SetupError(f"Setup failed during {stage}: {detail}") from exc


def solve_and_load(model, solver=None):
    """Check optimal termination before loading a solution or evaluating it."""
    import pyomo.environ as pyo
    solver = pyo.SolverFactory("appsi_highs") if solver is None else solver
    result = solver.solve(model, load_solutions=False)
    pyo.assert_optimal_termination(result)
    model.solutions.load_from(result)
    return result


def relax_integrality(model):
    """Relax all integer domains in place, including fixed binary variables."""
    import pyomo.environ as pyo
    pyo.TransformationFactory("core.relax_integer_vars").apply_to(model)
    return model


def solve(model, time_limit=180, tee=False, options=None):
    """Solve an LP/MILP with HiGHS and return a status-aware numerical report.

    The keys are ``status``, ``objective``, ``time``, ``nodes``, ``bound`` and
    ``gap``. Only an optimal report certifies an optimum. A limited solve may
    load an incumbent without proving optimality; no incumbent means objective
    is None. The bound is the solver's best proven bound, not the plain LP value.
    Solve a fresh model for each experiment. ``gap`` is a fraction, not percent.

    The tested highspy interface supplies the node count and MIP bound inside
    this helper; notebooks need not access solver internals. Duals are loaded
    only for an optimal continuous model with an IMPORT suffix.
    """
    import pyomo.environ as pyo
    if time_limit <= 0 or not math.isfinite(time_limit):
        raise ValueError("time_limit must be finite and positive")
    opt = pyo.SolverFactory("appsi_highs")
    opt.options.update(options or {})
    is_mip = any(v.is_integer() or v.is_binary()
                 for v in model.component_data_objects(pyo.Var, active=True))
    has_free_integer = any((v.is_integer() or v.is_binary()) and not v.fixed
                           for v in model.component_data_objects(pyo.Var, active=True))
    suffix = getattr(model, "dual", None)
    suffix = suffix if isinstance(suffix, pyo.Suffix) else None
    direction = suffix.direction if suffix is not None else None
    if suffix is not None:
        suffix.direction = pyo.Suffix.LOCAL
        suffix.clear()
    start = time.perf_counter()
    try:
        result = opt.solve(model, load_solutions=False, tee=tee, timelimit=time_limit)
    finally:
        if suffix is not None:
            suffix.direction = direction
    elapsed = time.perf_counter() - start
    termination = result.solver.termination_condition
    status = {
        pyo.TerminationCondition.optimal: "optimal",
        pyo.TerminationCondition.maxTimeLimit: "time_limit",
        pyo.TerminationCondition.infeasible: "infeasible",
        pyo.TerminationCondition.unbounded: "unbounded",
    }.get(termination, "other")
    report = dict(status=status, objective=None, time=elapsed, nodes=None, bound=None, gap=None)
    info = opt._solver_model.getInfo()
    feasible = status not in ("infeasible", "unbounded") and info.primal_solution_status == 2
    if feasible:
        opt.load_vars()
        objective = next(model.component_data_objects(pyo.Objective, active=True))
        report["objective"] = float(pyo.value(objective))
        if suffix is not None and direction & pyo.Suffix.IMPORT and not is_mip and status == "optimal":
            for row, value in opt.get_duals().items():
                suffix[row] = value
    if has_free_integer:
        report["nodes"] = int(info.mip_node_count) if info.mip_node_count >= 0 else None
        bound = float(info.mip_dual_bound)
        report["bound"] = bound if status not in ("infeasible", "unbounded") and math.isfinite(bound) else None
        gap = float(info.mip_gap)
        report["gap"] = gap if feasible and math.isfinite(gap) else None
    else:
        report.update(nodes=0, bound=report["objective"] if status == "optimal" else None,
                      gap=0.0 if status == "optimal" else None)
    return report


def format_number(value, digits=4):
    """Format text without changing a decision; suppress a rounded signed zero."""
    rounded = round(float(value), digits)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{digits}f}"
