import sympy as sp
import numpy as np

def plot_feasible_region(constraints, x_axis=None, y_axis=None, origin=(0,0), **kwargs):
    return sp.plot_implicit(sp.And(*constraints), x_axis, y_axis, axis_center=origin, line_color="lightblue", **kwargs)

def plot_objective(feasible_region_plot, objective_function, objective_values=None, **kwargs):
    """Add an objective curve/level sets using the plot's actual axis symbols."""
    if not hasattr(objective_values, "__iter__"):
        objective_values = [objective_values]
    objective_values = list(objective_values)
    if not objective_values:
        raise ValueError("objective_values must not be empty.")
    x_range, y_range = feasible_region_plot[0].ranges
    x_axis = (x_range[0],) + feasible_region_plot.xlim
    y_axis = (y_range[0],) + feasible_region_plot.ylim

    show = kwargs.pop("show", True)
    line_color = kwargs.pop("line_color", "blue")

    if len(objective_function.free_symbols | feasible_region_plot[0].expr.free_symbols) == 1:
        objective_plots = [sp.plot(objective_function, x_axis, ylim=y_axis[1:], 
                                      line_color="blue", show=False, **kwargs)[0]]
        if objective_values[0] is not None:
            objective_plots += [sp.plot_implicit(sp.Eq(y_axis[0], v), x_axis, y_axis,
                                      line_color=line_color, show=False, **kwargs)[0]
                                for v in objective_values]
    else:
        if any(v is None for v in objective_values):
            raise ValueError("Provide objective values for a multivariable objective.")
        objective_plots = [sp.plot_implicit(sp.Eq(objective_function, v), x_axis, y_axis, 
                                            line_color=line_color, show=False, **kwargs)[0] 
                          for v in objective_values]
       
    feasible_region_plot.extend(objective_plots)
    if show:
        feasible_region_plot.show()
        
def generateinstance(m, n, seed):
    """Generate a seeded full-column-rank matrix and box bounds (m >= n > 0).

    Kept for compatibility with existing notebook imports. The ten notebooks do
    not currently call it; new regression examples can use make_regression.
    """
    if not all(isinstance(k, (int, np.integer)) and not isinstance(k, (bool, np.bool_))
               and k > 0 for k in (m, n)):
        raise ValueError("m and n must be positive integers.")
    if m < n:
        raise ValueError("Full column rank requires m >= n.")
    rng = np.random.default_rng(seed)
    for _ in range(10):
        A = rng.random([m,n])
        if np.linalg.matrix_rank(A) == n:
            break
    else:
        raise RuntimeError("Could not generate a full-column-rank matrix after 10 attempts.")
    b = rng.random(m)
    l = - abs(5*rng.random(n))
    u = abs(5*rng.random(n))
    
    return A, b, l, u
