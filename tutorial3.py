import pyomo.environ as pyo
from IPython.display import Markdown, display
import math


def add_dual_variables(model):
    """Use this function before solving the model"""
    suffix = getattr(model, "dual", None)
    if suffix is None:
        model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    elif isinstance(suffix, pyo.Suffix):
        suffix.direction = pyo.Suffix.IMPORT
    else:
        raise TypeError("model.dual already exists and is not a Pyomo Suffix.")


def display_dual_variables(model):
    """Display imported raw RHS duals, preserving each row's sign convention.

    Indexed constraints and active constraints in nested blocks are supported.
    Missing duals are reported as unavailable, never replaced with zero.
    """
    display(Markdown("**Constraint duals (raw RHS convention):**"))
    dual = getattr(model, "dual", None)
    is_mip = any(v.is_integer() or v.is_binary()
                 for v in model.component_data_objects(pyo.Var, active=True))
    if is_mip:
        display(Markdown("LP duals are unavailable for a model with integer domains. "
                         "Fix the discrete design and solve its continuous model first."))
    for c in model.component_data_objects(pyo.Constraint, active=True, descend_into=True):
        value = dual.get(c) if isinstance(dual, pyo.Suffix) and not is_mip else None
        if value is None or not math.isfinite(float(value)):
            text = "unavailable (no imported dual for this row)"
        else:
            # Round for presentation only; do not alter the stored multiplier.
            shown = 0.0 if abs(value) < 0.0005 else value
            text = f"{shown:.3f}"
        display(Markdown(f"`{c.name}`: `{c.expr}`; raw dual **{text}**."))
