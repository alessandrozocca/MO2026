"""Shared assignment utilities: seeding, solving with HiGHS, and formatting answer blocks."""

import hashlib
import json
import time

import numpy as np
import pyomo.environ as pyo

ANSWERS_BEGIN = "=== MO2026 ANSWERS BEGIN ==="
ANSWERS_END = "=== MO2026 ANSWERS END ==="


def personal_seed(student_number, assignment):
    """Return the random seed of your personal instance (an integer derived from your student number).

    Use your VU student number (digits only), e.g. 2712345. Only if the teachers tell you so, add a variant
    suffix, e.g. "2712345-1"."""
    s = str(student_number).strip()
    number, _, variant = s.partition("-")
    if not number.isdigit() or len(number) < 5 or (variant and not variant.isdigit()):
        raise ValueError("STUDENT_NUMBER must be your VU student number (digits only), e.g. 2712345.")
    tag = f"{int(number)}" + (f"-{int(variant)}" if variant and int(variant) else "")
    digest = hashlib.sha256(f"MO2026|{assignment}|{tag}".encode()).hexdigest()
    return int(digest[:8], 16)


def solve(model, time_limit=180, tee=False, options=None):
    """Solve a Pyomo model with HiGHS and load the solution (and duals, if the model has a `dual` suffix).

    `options` is an optional dictionary of HiGHS options, e.g. {"mip_max_nodes": 1} to stop after the root node.
    Returns a dictionary with keys
      - 'status': 'optimal', 'time_limit' (a feasible solution was found but not proven optimal),
        'infeasible', 'unbounded' or 'other';
      - 'objective': objective value of the loaded solution (None if no solution was found);
      - 'time': wall-clock solving time in seconds;
      - 'nodes': number of branch-and-bound nodes (0 for an LP);
      - 'bound': best proven bound on the optimal value (equal to the objective for a solved LP);
      - 'gap': relative MIP gap (0 for an LP).
    """
    opt = pyo.SolverFactory("appsi_highs")
    for key, val in (options or {}).items():
        opt.options[key] = val
    is_mip = any(v.is_integer() or v.is_binary() for v in model.component_data_objects(pyo.Var, active=True))
    dual_suffix = getattr(model, "dual", None)
    if not isinstance(dual_suffix, pyo.Suffix):
        dual_suffix = None
    if dual_suffix is not None:  # duals are loaded below (only for LPs)
        dual_suffix.direction = pyo.Suffix.LOCAL
    start = time.perf_counter()
    try:
        res = opt.solve(model, tee=tee, timelimit=time_limit, load_solutions=False)
    finally:
        if dual_suffix is not None:
            dual_suffix.direction = pyo.Suffix.IMPORT
    elapsed = time.perf_counter() - start
    tc = res.solver.termination_condition
    status = {
        pyo.TerminationCondition.optimal: "optimal",
        pyo.TerminationCondition.maxTimeLimit: "time_limit",
        pyo.TerminationCondition.infeasible: "infeasible",
        pyo.TerminationCondition.unbounded: "unbounded",
        pyo.TerminationCondition.infeasibleOrUnbounded: "infeasible",
    }.get(tc, "other")
    out = {"status": status, "objective": None, "time": elapsed, "nodes": None, "bound": None, "gap": None}
    info = opt._solver_model.getInfo()
    # load the solution if HiGHS has a feasible point (also after a time or node limit)
    has_solution = status not in ("infeasible", "unbounded") and info.primal_solution_status == 2
    if has_solution:
        try:
            opt.load_vars()
        except Exception:
            has_solution = False
    if has_solution:
        out["objective"] = pyo.value(next(model.component_data_objects(pyo.Objective, active=True)))
        if dual_suffix is not None:
            dual_suffix.clear()
            if is_mip:
                print("Note: the model has integer/binary variables, so HiGHS returns no dual values. "
                      "Relax the integrality first (e.g. with relax_integrality) if you need duals.")
            elif status == "optimal":
                for con, val in opt.get_duals().items():
                    dual_suffix[con] = val
    if is_mip:
        out["nodes"] = int(info.mip_node_count)
        out["bound"] = float(info.mip_dual_bound)
        out["gap"] = float(info.mip_gap) if out["objective"] is not None else None
    else:
        out["nodes"] = 0
        out["bound"] = out["objective"]
        out["gap"] = 0.0 if out["objective"] is not None else None
    return out


def relax_integrality(model):
    """Turn all integer/binary variables of `model` into continuous ones (in place): the LP relaxation."""
    pyo.TransformationFactory("core.relax_integer_vars").apply_to(model)
    return model


def _to_builtin(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray, tuple, set)):
        return [_to_builtin(v) for v in obj]
    if isinstance(obj, list):
        return [_to_builtin(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): _to_builtin(v) for k, v in obj.items()}
    return obj


def check_answer_format(answers, template):
    """Check required keys and basic value types, returning True if the format checks pass.

    This does not check numerical or mathematical correctness, feasibility, or optimality.
    Nested dictionaries are checked only for their outer type, not their contents.
    """
    problems = []
    for key, expected in template.items():
        if key not in answers:
            problems.append(f"missing key '{key}'")
            continue
        val = answers[key]
        if expected.endswith("_or_none"):
            if val is None:
                continue
            expected = expected[: -len("_or_none")]
        if val is None:
            problems.append(f"'{key}' is still None")
        elif expected == "id":
            continue
        elif expected == "number" and not isinstance(val, (int, float, np.integer, np.floating)):
            problems.append(f"'{key}' should be a number, got {type(val).__name__}")
        elif expected == "list" and not isinstance(val, (list, tuple, set, np.ndarray)):
            problems.append(f"'{key}' should be a list, got {type(val).__name__}")
        elif expected == "dict" and not isinstance(val, dict):
            problems.append(f"'{key}' should be a dict, got {type(val).__name__}")
    if problems:
        print("Your ANSWERS dictionary has missing entries or format problems:")
        for p in problems:
            print("  -", p)
    else:
        print("All required keys are present with the expected basic types.")
    print("Format check only: numerical and mathematical correctness have not been checked.")
    return not problems


def print_answer_block(answers):
    """Print a JSON answer block for the staff grader to read from saved notebook outputs.

    This does not check correctness, save the notebook, upload it, or submit anything.
    Save the notebook with its outputs and upload the .ipynb file to Canvas yourself.
    """
    print("Printing the answer block only. Save this notebook with its outputs and upload it to Canvas.")
    print(ANSWERS_BEGIN)
    print(json.dumps(_to_builtin(answers), indent=1, sort_keys=True))
    print(ANSWERS_END)
